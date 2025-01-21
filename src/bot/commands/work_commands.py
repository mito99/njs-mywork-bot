import logging
import os
from abc import ABC, abstractmethod

import requests

from bot.config import Config

logger = logging.getLogger(__name__)

class WorkCommand(ABC):
    """作業コマンドの抽象基底クラス"""

    @abstractmethod
    async def execute(self, client, message, say):
        """コマンドを実行する抽象メソッド"""
        pass

    @classmethod
    async def create(cls, command_text: str, config: Config) -> "WorkCommand":
        """コマンドに応じたコマンドを返すビルダーメソッド"""

        # コマンドテキストをスペースで分割
        parts = command_text.split()
        action = parts[0].upper() if len(parts) > 0 else None
        file_type = parts[1] if len(parts) > 1 else None
        file_name = parts[2] if len(parts) > 2 else None

        storage_types = list(config.application.storage.keys())
        if file_type not in storage_types:
            return UsageCommand(config)

        if action == "GET":
            if not file_name:
                return UsageCommand(config)
            return GetFileCommand(file_type, file_name, config)
        elif action == "LIST":
            return ListFileCommand(file_type, config)
        elif action == "PUT":
            return PutFileCommand(file_type, config)
        elif action == "DELETE":
            return DeleteFileCommand(file_type, file_name, config)

        return UsageCommand(config)


class DeleteFileCommand(WorkCommand):
    """ファイルを削除するコマンド"""

    def __init__(self, file_type: str, file_name: str, config: Config):
        self.file_type = file_type
        self.file_name = file_name
        self.config = config

    async def execute(self, client, message, say):
        """ファイルを削除します。"""
        storage_path = self.config.application.storage[self.file_type].path
        file_path = os.path.join(storage_path, self.file_name)
        os.remove(file_path)
        await say(f"{self.file_type}ファイルを削除しました。=> {file_path}")
        return


class UsageCommand(WorkCommand):
    """使用方法を表示するコマンド"""

    def __init__(self, config: Config):
        self.config = config

    async def execute(self, client, message, say):
        """使用方法を表示します。"""
        from bot.tools.work_tools.types import FileType

        usage_message = (
            "使用可能なコマンド:\n"
            "- `cmd get <ストレージ名> <ファイル名>`: ファイルを取得\n"
            "- `cmd put <ストレージ名>`: ファイルをアップロード\n"
            "- `cmd list <ストレージ名>`: ファイル一覧を表示\n"
            "- `cmd delete <ストレージ名> <ファイル名>`: ファイルを削除\n\n"
            "利用可能なストレージ名:\n"
            + "\n".join([f"- {storage.value}" for storage in FileType])
        )
        await say(f"使用方法:\n{usage_message}")


class GetFileCommand(WorkCommand):
    """ファイルを取得するコマンド"""

    def __init__(self, file_type: str, work_file_name: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path
        self.file_path = os.path.join(self.storage_path, work_file_name)

    async def execute(self, client, message, say):
        """ファイルをアップロードします。"""
        await say(f"{self.file_type}ファイルを取得します。")
        result = client.files_upload_v2(
            channel=message["channel"],
            file=self.file_path,
            initial_comment=f"{self.file_type}ファイルを送ります。",
        )
        return


class ListFileCommand(WorkCommand):
    """ファイル一覧を取得するコマンド"""

    def __init__(self, file_type: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path

    async def execute(self, client, message, say):
        """ファイル一覧を取得します。"""
        await say(f"{self.file_type}ファイル一覧を取得します。")
        file_list = os.listdir(self.storage_path)
        if len(file_list) == 0:
            await say(f"{self.file_type}ファイルはありません。")
            return

        file_list_str = "\n".join([f"・{file}" for file in file_list])
        await say(f"{self.file_type}ファイル一覧:\n{file_list_str}")
        return


class PutFileCommand(WorkCommand):
    """ファイルを置くコマンド"""

    def __init__(self, file_type: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path
        self.slack_bot_token = config.slack_bot_token

    async def execute(self, client, message, say):
        """ファイルを置きます。"""
        await say(f"{self.file_type}ファイルをアップロードします。")
        if message.get("files") and len(message["files"]) <= 0:
            await say("ファイルがありません。")
            return

        file = message["files"][0]
        file_url = file.get("url_private_download")
        if not file_url:
            await say("ファイルのURLが取得できません。")
            return

        filename = file.get("name")
        save_path = os.path.join(self.storage_path, filename)

        headers = {"Authorization": f"Bearer {self.slack_bot_token}"}
        response = requests.get(file_url, headers=headers)
        with open(save_path, "wb") as f:
            f.write(response.content)

        await say(f"{self.file_type}ファイルを置きました。=> {save_path}")
        return 