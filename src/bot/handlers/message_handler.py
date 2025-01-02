import logging

from slack_bolt import App

from bot.config import Config
from bot.handlers.validation import is_valid_message
from bot.services import SimpleChatbot

logger = logging.getLogger(__name__)


def register_message_handlers(app: App, config: Config):
    """メッセージ関連のイベントハンドラーを登録します。"""

    chatbot = SimpleChatbot(config)

    @app.message()
    def handle_hello(self, message, say, client):
        """挨拶メッセージの処理"""

        # メッセージの検証を行う
        if not is_valid_message(message, config):
            return

        self._send_message(client, message, say)

    def _send_message(self, client, message, say):
        """メッセージを送信します。"""

        user_id = message["user"]
        user_info = client.users_info(user=user_id)
        display_name = user_info["user"]["profile"]["display_name"]
        message_text = message["text"]

        # 初回メッセージの送信
        thread_ts = message.get("ts")
        initial_response = client.chat_postMessage(
            channel=message["channel"],
            text=f"...",
            thread_ts=thread_ts,
        )

        # ストリーミングで返答を送信
        for chunk in chatbot.stream_chat(message_text, display_name):
            client.chat_update(
                channel=message["channel"],
                ts=initial_response["ts"],
                text=chunk,
            )
