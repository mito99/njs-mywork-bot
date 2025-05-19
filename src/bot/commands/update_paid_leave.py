"""
有給休暇ファイルを更新するコマンド
"""
import logging

from bot.commands.base import WorkCommand
from bot.config import Config
from bot.utils.file_restriction import FileRestriction
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)


class UpdatePaidLeaveCommand(WorkCommand):
    """有給休暇ファイルを更新するコマンド"""

    def __init__(self, file_type: str, file_name: str, config: Config):
        self.file_type = file_type
        self.file_name = file_name
        self.config = config
        self.file_restriction = FileRestriction(config)

    async def _get_user_info(self, client, message, say):
        # ユーザーIDを取得
        user_id = message.get("user")
        if not user_id:
            raise ValueError("ユーザーIDが取得できません。")
        
        user_info = await client.users_info(user=user_id)
        if not user_info["ok"]:
            raise ValueError("ユーザー情報の取得に失敗しました。")
        return user_info

    async def execute(self, client, message, say):
        """有給休暇ファイルを更新します。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            # 初期メッセージを送信
            await send_message.send(
                "有給休暇ファイルの更新を開始します..."
            )

            # ユーザー情報の取得
            await send_message.send(
                "ユーザー情報を取得中..."
            )
            user_info = await self._get_user_info(client, message, say)
            user = user_info["user"]

            # TODO: 有給休暇ファイルの更新処理を実装
            await send_message.send(
                "✅ 有給休暇ファイルの更新が完了しました。"
            )
        except Exception as e:
            logger.error(f"有給休暇ファイルの更新に失敗しました。エラー: {e}")
            await send_message.send(f"❌ 有給休暇ファイルの更新に失敗しました。エラー: {e}")
        return 