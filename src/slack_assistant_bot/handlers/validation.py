import logging

from slack_assistant_bot.config import Config

logger = logging.getLogger(__name__)


def is_valid_message(message: dict, config: Config) -> bool:
    """メッセージの共通検証を行います。

    Args:
        message (dict): Slackメッセージオブジェクト
        config (Config): アプリケーション設定

    Returns:
        bool: メッセージが有効な場合はTrue
    """
    # アプリ起動前のメッセージには反応しない
    message_ts = float(message.get("ts", 0))
    if message_ts < config.startup_time:
        logger.info(
            f"アプリ起動前のメッセージには反応しない: {message_ts} < {config.startup_time}"
        )
        return False

    user_id = message["user"]
    if user_id != config.allowed_user:
        logger.info(f"許可されていないユーザーからのメッセージ: {user_id}")
        return False

    return True
