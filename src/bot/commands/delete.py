"""
ファイルを削除するコマンド
"""
import logging
import os

from bot.commands.base import WorkCommand
from bot.config import Config
from bot.utils.file_restriction import FileRestriction
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)


class DeleteFileCommand(WorkCommand):
    """ファイルを削除するコマンド"""

    def __init__(self, file_type: str, file_name: str, config: Config):
        self.file_type = file_type
        self.file_name = file_name
        self.config = config
        self.file_restriction = FileRestriction(config)

    async def execute(self, client, message, say):
        """ファイルを削除します。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        
        if not self.file_restriction.is_allowed(self.file_name):
            await send_message.send("❌ ファイル名が制約に違反しています。")
            return
        
        try:
            await send_message.send(f"{self.file_type}ファイルの削除を開始します...")
            storage_path = self.config.application.storage[self.file_type].path
            file_path = os.path.join(storage_path, self.file_name)
            os.remove(file_path)
            await send_message.send(f"✅ {self.file_type}ファイルを削除しました。=> {file_path}")
        except Exception as e:
            logger.error(f"ファイルの削除に失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイルの削除に失敗しました。エラー: {e}")
        return 