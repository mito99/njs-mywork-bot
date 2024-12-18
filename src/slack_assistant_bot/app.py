import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import Config
from .handlers.message_handler import register_message_handlers


def create_app(config: Config) -> App:
    """アプリケーションを作成し、ハンドラーを登録します。"""
    app = App(token=config.slack_bot_token)

    # 各種ハンドラーの登録
    register_message_handlers(app, config)

    return app


def start_socket_mode(app: App, config: Config):
    """Socket Modeでアプリケーションを起動します。"""
    handler = SocketModeHandler(app=app, app_token=config.slack_app_token)
    handler.start()
