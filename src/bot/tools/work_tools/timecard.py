import asyncio
import logging
from datetime import date, datetime
from typing import Any, ClassVar, Optional

from dateutil.relativedelta import relativedelta
from langchain_core.tools import BaseTool
from njs_mywork_tools.attendance.models.timecard_data import TimeCardDataList
from njs_mywork_tools.attendance.reader import GoogleTimeCardReader
from slack_sdk.web.async_client import AsyncWebClient

from bot.config import Config
from bot.utils.message import MessageSender

logger = logging.getLogger(__name__)

class GetTimecardDataTool(BaseTool):
    """
    指定された年月の勤怠データを取得します。
    """
    
    name: ClassVar[str] = "get_timecard_data"
    description: ClassVar[str] = "指定された年月のタイムカードデータを取得します"
    
    config: Optional[Config] = None
    client: Optional[AsyncWebClient] = None
    message: Optional[dict[str, Any]] = None
    send_message: MessageSender = None

    def __init__(self, config: Config, client: AsyncWebClient, message: dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = client
        self.message = message
        self.send_message = MessageSender(
            self.client, 
            self.message["channel"], 
            self.message.get("ts")
        )

    def _run(self, 
             year: int | None, 
             month: int
    ) -> TimeCardDataList:
        """
        タイムカードデータの取得処理を実行するメソッド。

        Args:
            year (int | None): 取得対象の年。Noneの場合は自動的に決定
            month (int): 取得対象の月

        Returns:
            TimeCardDataList: 取得したタイムカードデータのリスト

        Note:
            - 非同期メソッド _arun を同期的に実行するためのラッパーメソッド
            - asyncio.run() を使用して非同期メソッドを同期的に実行
            - エラーハンドリングは _arun メソッド内で行われる

        Raises:
            ValueError: タイムカードデータの取得中に発生する可能性のある例外
        """
        return asyncio.run(self._arun(year, month))

    async def _arun(self, 
             year: int | None, 
             month: int
    ) -> TimeCardDataList:
        """
        タイムカードデータを取得します。

        Args:
            year (int | None): 取得対象年。Noneの場合は自動的に決定されます
            month (int): 取得対象月

        Returns:
            TimeCardDataList: 取得したタイムカードデータのリスト

        Note:
            - 出力年が指定されていない場合、現在の月に基づいて自動的に決定されます
            - タイムカードデータはGoogleTimeCardReaderを使用して取得されます    
        """
        logger.info(
            "GetTimecardDataTool: "
            f"{year}, {month}"
        )
        
        # 更新対象年と更新対象月がfloatの場合があるのでintに変換
        year = int(year) if year else None
        month = int(month)
                
        # 対象月が現在の月より小さい場合は、前年を対象年とする
        # 対象月が現在の月より大きい場合は、当年を対象年とする
        if year is None:
            if datetime.now().month < month:
                year = datetime.now().year - 1
            else:
                year = datetime.now().year
        
        await self.send_message.send(
            f"対象年月: {year}/{month}\n"
            "タイムカードデータを取得開始...\n"
        )
        
        # 勤怠データを取得
        timecard_data_list = self._get_timecard_data(year, month)
        
        await self.send_message.send("タイムカードデータの取得が完了しました。")
        return timecard_data_list

    def _get_timecard_data(self, year: int, month: int) -> TimeCardDataList:
        # 取得範囲は月初から月末まで
        start_date = date(year, month, 1)
        end_date = date(year, month, 1) + relativedelta(months=1) - relativedelta(days=1)
        
        try:
            time_card_reader = GoogleTimeCardReader(
                credentials_path=self.config.google_sheet.credentials_path,
                spreadsheet_key=self.config.google_sheet.spreadsheet_key,
                ssl_certificate_validation=self.config.google_sheet.ssl_certificate_validation,
            )
            return time_card_reader.read_timecard_sheet(start_date, end_date)
        except Exception as e:
            logger.error(f"タイムカードデータの取得に失敗しました。エラー: {e}")
            raise ValueError(f"タイムカードデータの取得に失敗しました。エラー: {e}")

