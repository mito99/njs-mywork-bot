import logging
import os
import tempfile
from datetime import datetime
from typing import Any, ClassVar, Optional

from dateutil.relativedelta import relativedelta
from langchain_core.tools import BaseTool
from njs_mywork_tools.attendance.models import Employee
from njs_mywork_tools.attendance.reader import GoogleTimeCardReader
from njs_mywork_tools.attendance.writer import ExcelWriter
from slack_sdk import WebClient

from bot.config import Config

from .types import FileType

logger = logging.getLogger(__name__)

class CreateAttendanceSheetTool(BaseTool):
    name: ClassVar[str] = "create_attendance_sheet"
    description: ClassVar[str] = "勤怠表を新規作成します"
    
    config: Optional[Config] = None
    client: Optional[WebClient] = None
    message: Optional[dict[str, Any]] = None

    def __init__(self, config: Config, client: WebClient, message: dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = client
        self.message = message

    def _run(self, 
             user_name: str, 
             output_year: int | None, 
             output_month: int, 
             attendance_file_name: str
    ) -> str:
        # 出力年と出力月がfloatの場合があるのでintに変換
        output_year = int(output_year) if output_year else None
        output_month = int(output_month)
                
        # 出力月が現在の月より小さい場合は、前年を出力年とする
        # 出力月が現在の月より大きい場合は、当年を出力年とする
        if output_year is None:
            if datetime.now().month < output_month:
                output_year = datetime.now().year - 1
            else:
                output_year = datetime.now().year
        
        # 勤怠データを取得
        timecard_data_list = self._get_timecard_data(output_year, output_month)
        
        # 勤怠表ファイルを作成
        output_path = self._create_attendance_file(
            user_name=user_name,
            attendance_file_name=attendance_file_name,
            output_month=output_month,
            timecard_data_list=timecard_data_list
        )

        # 作成した勤怠表を送信
        self._send_attendance_file(output_path)


    def _send_attendance_file(self, output_path: str) -> None:
        """
        作成した勤怠表ファイルをSlackチャンネルに送信します。

        Args:
            output_path (str): 送信するファイルのパス

        Raises:
            ValueError: ファイル送信に失敗した場合
        """
        try:
            thread_ts = self.message.get("ts")
            self.client.files_upload_v2(
                channel=self.message["channel"],
                file=output_path,
                initial_comment=f"作成した勤怠表を送ります。",
                thread_ts=thread_ts
            )
        except Exception as e:
            logger.error(f"ファイルの送信に失敗しました。エラー: {e}")
            raise ValueError(f"ファイルの送信に失敗しました。エラー: {e}")
        
    def _create_attendance_file(
        self,
        user_name: str,
        attendance_file_name: str,
        output_month: int,
        timecard_data_list: list[Any]
    ) -> str:
        attendance_dir_path = self.config.application.storage[FileType.ATTENDANCE].path
        attendance_file_path = os.path.join(attendance_dir_path, attendance_file_name)
        
        output_path = f"{tempfile.mkdtemp()}/{attendance_file_name}"
        try:
            employee = Employee.from_full_name(user_name)
            writer = ExcelWriter(attendance_file_path, employee)
            writer.write_to_file(output_path, output_month, timecard_data_list)
            return output_path
        except Exception as e:
            os.unlink(output_path)
            logger.error(f"勤怠表ファイルの作成に失敗しました。エラー: {e}")
            raise ValueError(f"勤怠表ファイルの作成に失敗しました。エラー: {e}")
        
    def _get_timecard_data(self, output_year: int, output_month: int) -> list[Any]:
        # 勤怠の範囲は前月21日から当月20日まで
        end_date = datetime(output_year, output_month, 20).date()
        start_date = (end_date - relativedelta(months=1)).replace(day=21)
        
        try:
            time_card_reader = GoogleTimeCardReader(
                credentials_path=self.config.google_sheet.credentials_path,
                spreadsheet_key=self.config.google_sheet.spreadsheet_key,
                ssl_certificate_validation=self.config.google_sheet.ssl_certificate_validation,
            )
            return time_card_reader.read_timecard_sheet(start_date, end_date)
        except Exception as e:
            logger.error(f"勤怠データの取得に失敗しました。エラー: {e}")
            raise ValueError(f"勤怠データの取得に失敗しました。エラー: {e}")