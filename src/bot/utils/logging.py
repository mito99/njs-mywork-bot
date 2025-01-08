import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """アプリケーションのログ設定を初期化します。

    Args:
        log_level (str): ログレベル（デフォルト: "INFO"）
        log_dir (str): ログファイルを保存するディレクトリ（デフォルト: "logs"）
    """
    # ログディレクトリの作成
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 文字列をログレベルに変換
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # コンソール出力の設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    # ファイル出力の設定（ローテーション付き）
    file_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)
