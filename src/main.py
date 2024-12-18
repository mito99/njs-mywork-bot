from datetime import datetime

from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_assistant_bot.app import create_app
from slack_assistant_bot.config import load_config
from slack_assistant_bot.utils.logging import setup_logging


def main():
    # ログ設定の初期化
    setup_logging()

    # 設定の読み込み
    config = load_config()

    # アプリケーションの作成と起動
    app = create_app(config)
    SocketModeHandler(app, config.slack_app_token).start()


if __name__ == "__main__":
    main()
