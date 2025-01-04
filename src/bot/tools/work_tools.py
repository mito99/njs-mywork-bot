from enum import Enum
import logging
import os
from typing import Any, ClassVar, Optional
import subprocess
from langchain_core.tools import BaseTool
from pydantic import Field
import requests
from slack_bolt import Say
from slack_sdk import WebClient

from bot.config import Config

logger = logging.getLogger(__name__)

class FileType(str, Enum):
    ATTENDANCE = "勤怠"
    HOLIDAY = "有休"

class CreateAttendanceSheetTool(BaseTool):
    name: ClassVar[str] = "create_attendance_sheet"
    description: ClassVar[str] = "勤怠表を新規作成します"

    def _run(self) -> str:
        """
        新しい勤怠表を作成し、そのファイルパスを返します。

        Returns:
            str: 作成された勤怠表のファイルパス
        """
        return "storage/local/kintai.md"

class SendFileTool(BaseTool):
    name: ClassVar[str] = "send_file"
    description: ClassVar[str] = "指定されたファイルを送信します。"

    config: Optional[Config] = None
    client: Optional[WebClient] = None
    message: Optional[dict[str, Any]] = None
    say: Optional[Say] = None

    def __init__(
        self, 
        config: Optional[Config] = None, 
        client: Optional[WebClient] = None, 
        message: Optional[dict[str, Any]] = None, 
        say: Optional[Say] = None,
    ):
        super().__init__()
        self.config = config
        self.client = client
        self.message = message
        self.say = say

    def _run(self, file_name: str, file_type: FileType):
        """
        指定されたファイルをSlackチャンネルに送信します。

        Args:
            file_name (str): 送信するファイル名
            file_type (FileType): ファイルの種類を示す列挙型

        Raises:
            ValueError: Slackクライアントまたはメッセージが設定されていない場合
        """
        if not self.client or not self.message:
            raise ValueError("Slack client or message is not configured")
        
        dir_path = self.config.application.storage[file_type].path
        resolved_file_path = os.path.abspath(f'{dir_path}/{file_name}')

        # ファイルの存在と有効性を確認
        if not os.path.exists(resolved_file_path):
            raise ValueError(f"ファイルが見つかりません: {resolved_file_path}")
        
        if os.path.getsize(resolved_file_path) == 0:
            raise ValueError(f"ファイルサイズが0バイトです: {resolved_file_path}")

        try:
            thread_ts = self.message.get("ts")
            self.client.files_upload_v2(
                channel=self.message["channel"],
                file=resolved_file_path,
                initial_comment=f"{file_type}/{file_name}を送ります。",
                thread_ts=thread_ts
            )
        except Exception as e:
            logger.error(f"ファイルの送信に失敗しました。エラー: {e}")
            raise ValueError(f"ファイルの送信に失敗しました。エラー: {e}")

class ReceiveFileTool(BaseTool):
    name: ClassVar[str] = "receive_file"
    description: ClassVar[str] = "ファイルを受信します"

    config: Optional[Config] = None
    message: Optional[dict[str, Any]] = None
    say: Optional[Say] = None

    def __init__(self, config: Config, message: dict[str, Any], say: Say):
        super().__init__()
        self.config = config
        self.message = message
        self.say = say

    def _run(self, file_name: str, file_type: FileType):
        """
        Slackから指定されたファイルを受信し、指定されたストレージディレクトリに保存します。

        Args:
            file_name (str): 保存するファイル名
            file_type (FileType): ファイルの種類を示す列挙型

        Returns:
            str: 保存されたファイルの完全パス

        Raises:
            ValueError: ファイルが存在しない、またはファイルのURLが取得できない場合
        """
        if self.message.get("files") and len(self.message["files"]) <= 0:
            raise ValueError("ファイルがありません。")

        file = self.message["files"][0]
        file_url = file.get("url_private_download")
        if not file_url:
            raise ValueError("ファイルのURLが取得できません。")

        filename = file.get("name")
        dir_path = self.config.application.storage[file_type].path
        save_path = os.path.join(dir_path, filename)

        headers = {"Authorization": f"Bearer {self.config.slack_bot_token}"}
        response = requests.get(file_url, headers=headers)
        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path

class ListFilesTool(BaseTool):
    name: ClassVar[str] = "list_files"
    description: ClassVar[str] = "ファイルの一覧を取得します"

    config: Optional[Config] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, file_type: FileType) -> list[str]:
        """
        指定されたファイルタイプのディレクトリ内のファイル一覧を取得します。

        Args:
            file_type (FileType): 取得するファイルの種類を指定する列挙型

        Returns:
            list[str]: ファイル名のリスト。
                       ディレクトリが存在しない、またはコマンド実行に失敗した場合は空のリストを返します。

        Note:
            - lsコマンドを使用してファイル一覧を取得します。
            - サブディレクトリ内のファイルは含まれません。
        """
        dir_path = self.config.application.storage[file_type].path
        result = subprocess.run(
            f"ls {dir_path}/*",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return []
        return [os.path.basename(file) for file in result.stdout.strip().split("\n")]