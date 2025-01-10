import logging

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from .config import Config
from .handlers import register_work_handlers


def create_app(config: Config) -> AsyncApp:
    """アプリケーションを作成し、ハンドラーを登録します。"""
    app = AsyncApp(token=config.slack_bot_token)

    # 各種ハンドラーの登録
    # register_message_handlers(app, config)
    register_work_handlers(app, config)

    return app


async def start_socket_mode(app: AsyncApp, config: Config):
    """Socket Modeでアプリケーションを起動します。"""
    client = AsyncWebClient()
    handler = AsyncSocketModeHandler(
        app_token=config.slack_app_token,
        app=app,
        web_client=client
    )
    await handler.start_async()
