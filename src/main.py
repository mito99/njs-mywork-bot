import logging
from time import sleep

from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_assistant_bot.app import create_app
from slack_assistant_bot.config import load_config
from slack_assistant_bot.utils.logging import setup_logging


def start_handler(app, app_token, max_retries=None):
    while True:
        try:
            handler = SocketModeHandler(app, app_token)
            handler.start()
        except Exception as e:
            logging.error(f"Socket Mode接続エラー: {e}")
            if max_retries is not None:
                max_retries -= 1
                if max_retries <= 0:
                    raise
            logging.info("5秒後に再接続を試みます...")
            sleep(5)


def main():
    config = load_config()
    setup_logging(config.log_level)
    app = create_app(config)

    # 再接続ロジックを含むハンドラーの起動
    start_handler(app, config.slack_app_token)


if __name__ == "__main__":
    main()
