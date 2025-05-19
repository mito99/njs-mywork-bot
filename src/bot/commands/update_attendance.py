"""
勤怠表を更新するコマンド
"""
import logging

from bot.commands.base import WorkCommand
from bot.config import Config
from bot.tools.work_tools.attendance import UpdateAttendanceSheetTool
from bot.utils.file_restriction import FileRestriction
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)


class UpdateAttendanceCommand(WorkCommand):
    """勤怠表を更新するコマンド"""

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
        """勤怠表を更新します。"""
        thread_ts = message.get("ts")
        send_message = MessageSender(client, message["channel"], thread_ts)
        try:
            # 初期メッセージを送信
            await send_message.send(
                "勤怠表の更新を開始します..."
            )

            # ユーザー情報の取得
            await send_message.send(
                "ユーザー情報を取得中..."
            )
            user_info = await self._get_user_info(client, message, say)
            user = user_info["user"]

            # 勤怠表の更新
            await send_message.send(
                "勤怠表を更新中..."
            )
            tool = UpdateAttendanceSheetTool(self.config)
            tool.update(user)

            await send_message.send(
                "✅ 勤怠表の更新が完了しました。"
            )
        except Exception as e:
            logger.error(f"勤怠表の更新に失敗しました。エラー: {e}")
            await send_message.send(f"❌ 勤怠表の更新に失敗しました。エラー: {e}")
        return 