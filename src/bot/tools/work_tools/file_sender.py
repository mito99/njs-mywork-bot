import asyncio
import logging
import os
from pathlib import Path
from typing import Any, ClassVar, Optional

from langchain_core.tools import BaseTool
from slack_sdk.web.async_client import AsyncWebClient

from bot.config import Config

from .types import FileType

logger = logging.getLogger(__name__)

class SendFileTool(BaseTool):
    name: ClassVar[str] = "send_file"
    description: ClassVar[str] = "指定されたファイルを送信します。"

    config: Optional[Config] = None
    client: Optional[AsyncWebClient] = None
    message: Optional[dict[str, Any]] = None

    def __init__(
        self, 
        config: Optional[Config] = None, 
        client: Optional[AsyncWebClient] = None, 
        message: Optional[dict[str, Any]] = None, 
    ):
        super().__init__()
        self.config = config
        self.client = client
        self.message = message

    def _run(self, file_name: str, file_type: FileType):
        """
        指定されたファイルをSlackに送信するためのメソッド。

        Args:
            file_name (str): 送信するファイルの名前
            file_type (FileType): 送信するファイルの種類（ストレージカテゴリ）

        Note:
            - 非同期メソッド _arun を実行するためのラッパーメソッド
            - asyncio.run() を使用して非同期メソッドを同期的に実行
            - エラーハンドリングは _arun メソッド内で行われる

        Raises:
            ValueError: ファイル送信中に発生する可能性のある例外
        """
        asyncio.run(self._arun(file_name, file_type))

    async def _arun(self, file_name: str, file_type: FileType):
        """
        指定されたファイルをSlackチャンネルに送信します。

        Args:
            file_name (str): 送信するファイルの名前
            file_type (FileType): 送信するファイルの種類（ストレージカテゴリ）

        Raises:
            ValueError: Slack clientまたはmessageが設定されていない場合
                        ファイルが見つからない場合
                        ファイルサイズが0バイトの場合
                        ファイル送信に失敗した場合

        Note:
            - ファイルは指定されたストレージディレクトリから取得されます。
            - ファイルはSlackのスレッドに送信されます。
        """
        logger.info(f"SendFileTool: {file_name}, {file_type}")
        
        if not self.client or not self.message:
            raise ValueError("Slack client or message is not configured")
        
        dir_path = self.config.application.storage[file_type].path
        resolved_file_path = Path(dir_path) / file_name

        # ファイルの存在と有効性を確認
        if not Path(resolved_file_path).exists():
            raise ValueError(f"ファイルが見つかりません: {resolved_file_path}")
        
        if Path(resolved_file_path).stat().st_size == 0:
            raise ValueError(f"ファイルサイズが0バイトです: {resolved_file_path}")

        try:
            thread_ts = self.message.get("ts")
            # ファイルを開いてバイナリモードで読み込む
            with open(resolved_file_path, 'rb') as file:
                await self.client.files_upload_v2(
                    channel=self.message["channel"],
                    file=file,
                    filename=file_name,
                    initial_comment=f"{file_type}/{file_name}を送ります。",
                    thread_ts=thread_ts
                )
        except Exception as e:
            logger.error(f"ファイルの送信に失敗しました。エラー: {e}")
            raise ValueError(f"ファイルの送信に失敗しました。エラー: {e}") 