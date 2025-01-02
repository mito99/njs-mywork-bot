from pathlib import Path
from typing import Callable, Iterator

from bot.config import Config


class WorkChatbot:
    """ワークチャットボットのサービス"""

    def __init__(self, config: Config):
        self.config = config

    def chat(
        self, message: str, user_id: str, on_upload_file: Callable[[str, Path], None]
    ) -> None:
        if message == "勤怠ファイル取得して":
            on_upload_file("どうぞ！", Path("./README.md"))
