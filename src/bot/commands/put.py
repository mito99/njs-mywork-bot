"""
ファイルを置くコマンド
"""
import logging
import os

import requests

from bot.commands.base import WorkCommand
from bot.config import Config
from bot.utils.file_restriction import FileRestriction
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)


class PutFileCommand(WorkCommand):
    """ファイルを置くコマンド"""

    def __init__(self, file_type: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path
        self.slack_bot_token = config.slack_bot_task.bot_token
        self.file_restriction = FileRestriction(config)

    async def execute(self, client, message, say):
        """ファイルを置きます。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            await send_message.send(f"{self.file_type}ファイルのアップロードを開始します...")
            if message.get("files") and len(message["files"]) <= 0:
                await send_message.send("❌ ファイルがありません。")
                return

            file = message["files"][0]
            file_url = file.get("url_private_download")
            if not file_url:
                await send_message.send("❌ ファイルのURLが取得できません。")
                return

            filename = file.get("name")
            save_path = os.path.join(self.storage_path, filename)
            if not self.file_restriction.is_allowed(filename):
                await send_message.send("❌ ファイル名が制約に違反しています。")
                return

            headers = {"Authorization": f"Bearer {self.slack_bot_token}"}
            response = requests.get(file_url, headers=headers)
            with open(save_path, "wb") as f:
                f.write(response.content)

            await send_message.send(f"✅ {self.file_type}ファイルを置きました。=> {save_path}")
        except Exception as e:
            logger.error(f"ファイルのアップロードに失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイルのアップロードに失敗しました。エラー: {e}")
        return 