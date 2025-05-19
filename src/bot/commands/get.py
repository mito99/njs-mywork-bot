"""
ファイルを取得するコマンド
"""
import logging
import os

from bot.commands.base import WorkCommand
from bot.config import Config
from bot.utils.file_restriction import FileRestriction
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)


class GetFileCommand(WorkCommand):
    """ファイルを取得するコマンド"""

    def __init__(self, file_type: str, work_file_name: str, config: Config):
        self.file_type = file_type
        self.storage_path = config.application.storage[file_type].path
        self.file_path = os.path.join(self.storage_path, work_file_name)
        self.file_restriction = FileRestriction(config)

    async def execute(self, client, message, say):
        """ファイルをアップロードします。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        
        if not self.file_restriction.is_allowed(self.file_path):
            await send_message.send("❌ ファイル名が制約に違反しています。")
            return
        
        try:
            await send_message.send(f"{self.file_type}ファイルの取得を開始します...")
            await client.files_upload_v2(
                channel=message["channel"],
                file=self.file_path,
                filename=os.path.basename(self.file_path),
                initial_comment=f"{self.file_type}ファイルを送ります。",
                thread_ts=thread_ts
            )
            await send_message.send("✅ ファイルの取得が完了しました")
        except Exception as e:
            logger.error(f"ファイルの取得に失敗しました。エラー: {e}")
            await send_message.send(f"❌ ファイルの取得に失敗しました。エラー: {e}")
        return 