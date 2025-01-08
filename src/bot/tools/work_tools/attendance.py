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

class UpdateAttendanceSheetTool(BaseTool):
    """
    勤怠表を更新します。
    """
    
    name: ClassVar[str] = "update_attendance_sheet"
    description: ClassVar[str] = "勤怠表を更新します"
    
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
             update_year: int | None, 
             update_month: int, 
             attendance_file_name: str
    ) -> str:
        """
        勤怠ファイルを更新します。

        Args:
            user_name (str): 更新する対象の勤怠表の従業員名
            update_year (int | None): 更新対象年。Noneの場合は自動的に決定されます
            update_month (int): 更新対象月
            attendance_file_name (str): 更新対象勤怠表のファイル名

        Returns:
            str: 作成された勤怠表のファイルパス

        Note:
            - 出力年が指定されていない場合、現在の月に基づいて自動的に決定されます
            - 勤怠データはGoogleTimeCardReaderを使用して取得されます
            - 勤怠表はExcelWriterを使用して作成されます
        """
        
        logger.info(
            "UpdateAttendanceSheetTool: "
            f"{user_name}, {update_year}, {update_month}, {attendance_file_name}"
        )
        
        # 更新対象年と更新対象月がfloatの場合があるのでintに変換
        update_year = int(update_year) if update_year else None
        update_month = int(update_month)
                
        # 更新対象月が現在の月より小さい場合は、前年を更新対象年とする
        # 更新対象月が現在の月より大きい場合は、当年を更新対象年とする
        if update_year is None:
            if datetime.now().month < update_month:
                update_year = datetime.now().year - 1
            else:
                update_year = datetime.now().year
        
        # 勤怠データを取得
        logger.info(f"UpdateAttendanceSheetTool: {update_year}, {update_month}")
        timecard_data_list = self._get_timecard_data(update_year, update_month)
        
        # 一時ディレクトリに勤怠表ファイルを作成
        output_path = self._update_attendance_file(
            user_name=user_name,
            attendance_file_name=attendance_file_name,
            update_month=update_month,
            timecard_data_list=timecard_data_list
        )

        # 更新した勤怠表を送信
        logger.info(f"UpdateAttendanceSheetTool: {output_path}")
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
                initial_comment=f"更新した勤怠表を送ります。",
                thread_ts=thread_ts
            )
        except Exception as e:
            logger.error(f"ファイルの送信に失敗しました。エラー: {e}")
            raise ValueError(f"ファイルの送信に失敗しました。エラー: {e}")
        
    def _update_attendance_file(
        self,
        user_name: str,
        attendance_file_name: str,
        update_month: int,
        timecard_data_list: list[Any]
    ) -> str:
        attendance_dir_path = self.config.application.storage[FileType.ATTENDANCE].path
        attendance_file_path = os.path.join(attendance_dir_path, attendance_file_name)
        
        # update_path = f"{tempfile.mkdtemp()}/{attendance_file_name}"
        update_path = attendance_file_path
        try:
            employee = Employee.from_full_name(user_name)
            writer = ExcelWriter(attendance_file_path, employee)
            writer.write_to_file(update_path, update_month, timecard_data_list)
            return update_path
        except Exception as e:
            os.unlink(update_path)
            logger.error(f"勤怠表ファイルの作成に失敗しました。エラー: {e}")
            raise ValueError(f"勤怠表ファイルの作成に失敗しました。エラー: {e}")
        
    def _get_timecard_data(self, update_year: int, update_month: int) -> list[Any]:
        # 勤怠の範囲は前月21日から当月20日まで
        end_date = datetime(update_year, update_month, 20).date()
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