import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging():
    """アプリケーションのログ設定を初期化します。"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # コンソール出力
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    # ファイル出力
    file_handler = RotatingFileHandler("app.log", maxBytes=1024 * 1024, backupCount=5)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)
