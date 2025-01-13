import logging

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from .config import Config
from .handlers import register_work_handlers


class SlackBotTaskApp:
    
    def __init__(self, config: Config):
        self.config = config
        self.app = self._create_app(config)

    async def start_socket_mode(self):
        handler = AsyncSocketModeHandler(
            app_token=self.config.slack_bot_task.app_token,
            app=self.app,
            web_client=AsyncWebClient()
        )
        await handler.start_async()

    def _create_app(self, config: Config) -> AsyncApp:
        """アプリケーションを作成し、ハンドラーを登録します。"""
        app = AsyncApp(token=config.slack_bot_task.bot_token)

        # 各種ハンドラーの登録
        # register_message_handlers(app, config)
        register_work_handlers(app, config)

        return app
