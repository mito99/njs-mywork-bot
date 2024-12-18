import logging

from slack_bolt import App

from slack_assistant_bot.config import Config

logger = logging.getLogger(__name__)


def register_message_handlers(app: App, config: Config):
    """メッセージ関連のイベントハンドラーを登録します。"""

    @app.message()
    def handle_hello(message, say):
        """挨拶メッセージの処理"""

        # アプリ起動前のメッセージには反応しない
        message_ts = float(message.get("ts", 0))
        if message_ts < config.startup_time:
            logger.info(
                f"アプリ起動前のメッセージには反応しない: {message_ts} < {config.startup_time}"
            )
            return

        if message["user"] != config.allowed_user:
            logger.info(f"許可されていないユーザーからのメッセージ: {message['user']}")
            return

        say(f"こんにちは、<@{message['user']}>さん！")
