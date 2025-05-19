"""
ファイル一覧を取得するコマンド
"""
import logging
import os

from bot.commands.base import WorkCommand
from bot.config import Config
from bot.utils.file_restriction import FileRestriction
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)


class ListFileCommand(WorkCommand):
    """ファイル一覧を取得するコマンド"""

    def __init__(self, file_type: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path
        self.file_restriction = FileRestriction(config)

    async def execute(self, client, message, say):
        """ファイル一覧を取得します。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            await send_message.send(f"{self.file_type}ファイル一覧の取得を開始します...")
            file_list = os.listdir(self.storage_path)            
            if len(file_list) == 0:
                await send_message.send(f"ℹ️ {self.file_type}ファイルはありません。")
                return

            file_list_str = "\n".join([f"・{file}" for file in file_list])
            await send_message.send(f"✅ {self.file_type}ファイル一覧:\n{file_list_str}")
        except Exception as e:
            logger.error(f"ファイル一覧の取得に失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイル一覧の取得に失敗しました。エラー: {e}")
        return 