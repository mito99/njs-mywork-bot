import logging
import os
from typing import Any, ClassVar, Optional

from langchain_core.tools import BaseTool
from slack_sdk import WebClient

from bot.config import Config

from .types import FileType

logger = logging.getLogger(__name__)

class SendFileTool(BaseTool):
    name: ClassVar[str] = "send_file"
    description: ClassVar[str] = "指定されたファイルを送信します。"

    config: Optional[Config] = None
    client: Optional[WebClient] = None
    message: Optional[dict[str, Any]] = None

    def __init__(
        self, 
        config: Optional[Config] = None, 
        client: Optional[WebClient] = None, 
        message: Optional[dict[str, Any]] = None, 
    ):
        super().__init__()
        self.config = config
        self.client = client
        self.message = message

    def _run(self, file_name: str, file_type: FileType):
        if not self.client or not self.message:
            raise ValueError("Slack client or message is not configured")
        
        dir_path = self.config.application.storage[file_type].path
        resolved_file_path = os.path.abspath(f'{dir_path}/{file_name}')

        # ファイルの存在と有効性を確認
        if not os.path.exists(resolved_file_path):
            raise ValueError(f"ファイルが見つかりません: {resolved_file_path}")
        
        if os.path.getsize(resolved_file_path) == 0:
            raise ValueError(f"ファイルサイズが0バイトです: {resolved_file_path}")

        try:
            thread_ts = self.message.get("ts")
            self.client.files_upload_v2(
                channel=self.message["channel"],
                file=resolved_file_path,
                initial_comment=f"{file_type}/{file_name}を送ります。",
                thread_ts=thread_ts
            )
        except Exception as e:
            logger.error(f"ファイルの送信に失敗しました。エラー: {e}")
            raise ValueError(f"ファイルの送信に失敗しました。エラー: {e}") 