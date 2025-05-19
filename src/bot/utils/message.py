import logging
from typing import Optional

from slack_sdk.web.async_client import AsyncWebClient

logger = logging.getLogger(__name__)

class MessageSender:
    """Slackメッセージ送信を抽象化するクラス"""
    
    def __init__(
        self, 
        client: AsyncWebClient, 
        channel: str, 
        thread_ts: Optional[str] = None
    ):
        """
        Args:
            client (AsyncWebClient): Slackクライアント
            channel (str): メッセージを送信するチャンネルID
            thread_ts (Optional[str]): スレッドのタイムスタンプ。Noneの場合は新規スレッド
        """
        self.client = client
        self.channel = channel
        self.thread_ts = thread_ts
    
    async def send(self, text: str) -> None:
        """
        メッセージを送信する

        Args:
            text (str): 送信するメッセージテキスト

        Raises:
            Exception: メッセージ送信に失敗した場合
        """
        try:
            await self.client.chat_postMessage(
                channel=self.channel,
                thread_ts=self.thread_ts,
                text=text
            )
        except Exception as e:
            logger.error(f"メッセージの送信に失敗しました: {e}")
            raise 