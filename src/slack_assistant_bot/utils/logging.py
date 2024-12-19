import logging
import sys


def setup_logging(log_level: str = "INFO"):
    """アプリケーションのログ設定を初期化します。"""
    # 文字列をログレベルに変換
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # コンソール出力のみ設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)
