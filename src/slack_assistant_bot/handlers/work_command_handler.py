import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import requests
from slack_bolt import App

from slack_assistant_bot.config import Config
from slack_assistant_bot.handlers.validation import is_valid_message
from slack_assistant_bot.services import SimpleChatbot

logger = logging.getLogger(__name__)

ALLOWED_MESSAGES = [
    "GET 勤怠ファイル <FILENAME>",
    "GET 勤怠ファイル一覧",
    "PUT 勤怠ファイル",
    "GET 有給休暇ファイル <FILENAME>",
    "GET 有給休暇ファイル一覧",
    "PUT 有給休暇ファイル",
]


def register_work_command_handlers(app: App, config: Config):
    """メッセージ関連のイベントハンドラーを登録します。"""

    @app.message()
    def handle_message(message, say, client):
        """挨拶メッセージの処理"""

        # メッセージの検証を行う
        if not is_valid_message(message, config):
            return

        # メッセージテキストを取得
        text = message.get("text", "").strip()
        command = WorkCommand.create(text, config)
        if not command:
            response = (
                "申し訳ありません。以下のいずれかのメッセージを送信してください：\n"
                + "\n".join([f"・{work}" for work in ALLOWED_MESSAGES])
            )
            say(response)
            return

        try:
            command.execute(client, message, say)
        except Exception as e:
            say(f"エラーが発生しました。\n{e}")
            return

    @app.event("message")
    def handle_message_events(body, logger):
        logger.debug(body)


@dataclass
class WorkFileInfo:
    local_dir_path: str
    file_type: str

    @classmethod
    def get(cls, filetype: str, config: Config) -> "WorkFileInfo":
        """ファイルの設定を取得します。"""
        match filetype:
            case "勤怠":
                return WorkFileInfo(
                    local_dir_path=config.work_report_storage_path.resolve(),
                    file_type="勤怠",
                )
            case "有給休暇":
                return WorkFileInfo(
                    local_dir_path=config.paid_leave_storage_path.resolve(),
                    file_type="有給休暇",
                )
            case _:
                raise ValueError(f"Invalid filetype: {filetype}")


class WorkCommand(ABC):
    """作業コマンドの抽象基底クラス"""

    @abstractmethod
    def execute(self, client, message, say, config):
        """コマンドを実行する抽象メソッド"""
        pass

    @classmethod
    def create(cls, command_text: str, config: Config) -> "WorkCommand":
        """コマンドに応じたコマンドを返すビルダーメソッド"""

        get_file_pattern = r"GET (勤怠|有給休暇)ファイル (\w+\.\w+)"
        get_file_match = re.match(get_file_pattern, command_text)
        if get_file_match:
            work_file_info = WorkFileInfo.get(get_file_match.group(1), config)
            work_file_name = os.path.basename(get_file_match.group(2))
            return GetFileCommand(work_file_info, work_file_name, config)

        put_file_pattern = r"PUT (勤怠|有給休暇)ファイル"
        put_file_match = re.match(put_file_pattern, command_text)
        if put_file_match:
            work_file_info = WorkFileInfo.get(put_file_match.group(1), config)
            return PutFileCommand(work_file_info, config)

        get_file_list_pattern = r"GET (勤怠|有給休暇)ファイル一覧"
        get_file_list_match = re.match(get_file_list_pattern, command_text)
        if get_file_list_match:
            work_file_info = WorkFileInfo.get(get_file_list_match.group(1), config)
            return GetFileListCommand(work_file_info, config)

        return None


class GetFileCommand(WorkCommand):
    """ファイルを取得するコマンド"""

    def __init__(self, info: WorkFileInfo, work_file_name: str, config: Config):
        self.info = info
        self.file_path = os.path.join(info.local_dir_path, work_file_name)
        self.config = config

    def execute(self, client, message, say, config):
        """ファイルをアップロードします。"""
        result = client.files_upload_v2(
            channel=message["channel"],
            file=self.file_path,
            initial_comment="勤怠ファイルを送ります。",
        )
        return


class GetFileListCommand(WorkCommand):
    """ファイル一覧を取得するコマンド"""

    def __init__(self, info: WorkFileInfo, config: Config):
        self.info = info
        self.config = config

    def execute(self, client, message, say):
        """ファイル一覧を取得します。"""
        file_list = os.listdir(self.info.local_dir_path)
        file_list_str = "\n".join([f"・{file}" for file in file_list])
        say(f"{self.info.file_type}ファイル一覧:\n{file_list_str}")
        return


class PutFileCommand(WorkCommand):
    """ファイルを置くコマンド"""

    def __init__(self, info: WorkFileInfo, config: Config):
        self.info = info
        self.config = config

    def execute(self, client, message, say):
        """ファイルを置きます。"""
        if message.get("files") and len(message["files"]) <= 0:
            say("ファイルがありません。")
            return

        file = message["files"][0]
        file_url = file.get("url_private_download")
        if not file_url:
            say("ファイルのURLが取得できません。")
            return

        filename = file.get("name")
        save_path = os.path.join(self.info.local_dir_path, filename)

        headers = {"Authorization": f"Bearer {self.config.slack_bot_token}"}
        response = requests.get(file_url, headers=headers)
        with open(save_path, "wb") as f:
            f.write(response.content)

        say(f"勤怠ファイルを置きました。=> {save_path}")
        return
