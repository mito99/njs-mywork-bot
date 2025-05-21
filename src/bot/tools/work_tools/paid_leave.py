import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, ClassVar, Optional

from dateutil.relativedelta import relativedelta
from langchain_core.tools import BaseTool
from njs_mywork_tools.attendance.models import PaidLeaveType, TimeCardDataList
from njs_mywork_tools.attendance.models.employee import Employee
from njs_mywork_tools.attendance.reader import (ExcelPaidLeaveReader,
                                                GoogleTimeCardReader)
from njs_mywork_tools.attendance.writer import ExcelPaidLeaveWriter
from slack_sdk.web import WebClient
from slack_sdk.web.async_client import AsyncWebClient

from bot.config import Config
from bot.tools.work_tools.types import FileType

logger = logging.getLogger(__name__)

class PaidLeaveStatus(Enum):
    """
    有給休暇の申請状態
    """
    PENDING = "申請中"  # 申請中
    APPROVED = "承認済"  # 承認済
    REJECTED = "却下"    # 却下


@dataclass
class PaidLeaveApplication:
    """
    有給休暇申請データ
    """
    application_date: date  # 申請日
    leave_type: PaidLeaveType  # 有給休暇の種類
    status: PaidLeaveStatus = PaidLeaveStatus.PENDING  # 申請状態
    reason: Optional[str] = None  # 申請理由
    created_at: datetime = datetime.now()  # 作成日時
    updated_at: datetime = datetime.now()  # 更新日時


class UpdatePaidLeaveTool(BaseTool):
    """
    有給休暇申請を更新します。
    """
    
    name: ClassVar[str] = "update_paid_leave"
    description: ClassVar[str] = "有給休暇申請を更新します。"

    config: Optional[Config] = None
    client: Optional[AsyncWebClient] = None
    message: Optional[dict[str, Any]] = None

    def __init__(self, config: Config, client: AsyncWebClient, message: dict[str, Any]):
        super().__init__()
        self.config = config
        self.client = client
        self.message = message

    def _run(self, 
             user_name: str, 
             update_year: int | None, 
             update_month: int, 
             paid_leave_file_name: str
    ) -> str:
        """
        有給休暇申請の更新処理を実行するメソッド。

        Args:
            user_name (str): 更新対象の従業員名
            update_year (int | None): 更新対象の年。Noneの場合は自動的に決定
            update_month (int): 更新対象の月
            paid_leave_file_name (str): 更新する有給休暇申請のファイル名

        Returns:
            str: 更新された有給休暇申請のファイルパス
        """
        asyncio.run(self._arun(user_name, update_year, update_month, paid_leave_file_name))

    async def _arun(self, 
             user_name: str, 
             update_year: int | None, 
             update_month: int, 
             paid_leave_file_name: str
    ) -> str:
        """
        有給休暇申請の更新処理を実行するメソッド。
        """
        # 有給休暇申請のファイルを読み込む
        logger.info(
            "UpdatePaidLeaveTool: "
            f"{user_name}, {update_year}, {update_month}, {paid_leave_file_name}"
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
        logger.info(f"UpdatePaidLeaveTool: {update_year}, {update_month}")
        timecard_data_list: TimeCardDataList = self._get_timecard_data(update_year, update_month)        
        self._update_paid_leave_file(user_name, paid_leave_file_name, update_month, timecard_data_list)

    def _update_paid_leave_file(
        self,
        user_name: str,
        paid_leave_file_name: str,
        update_month: int,
        timecard_data_list: TimeCardDataList
    ) -> str:
        """
        有給休暇申請ファイルを更新する
        """
        paid_leave_data_list: dict[date, PaidLeaveType] = {
            data.date: PaidLeaveType.FULL_DAY
            for data in timecard_data_list
            if data.work_type in ('有休', '有給')
        }
        
        paid_leave_dir_path = self.config.application.storage[FileType.HOLIDAY].path
        paid_leave_file_path = os.path.join(paid_leave_dir_path, paid_leave_file_name)
        
        # バックアップファイルを作成
        from bot.tools.work_tools import backup_file
        backup_file(paid_leave_file_path)
        
        update_path = paid_leave_file_path
        try:
            employee = Employee.from_full_name(user_name)
            with ExcelPaidLeaveWriter(paid_leave_file_path, employee) as writer:
                writer.add_paid_leave_applications(paid_leave_data_list)
            
            return update_path
        except Exception as e:
            # os.unlink(update_path)
            logger.error(f"有給休暇申請ファイルの作成に失敗しました。エラー: {e}")
            raise ValueError(f"有給休暇申請ファイルの作成に失敗しました。エラー: {e}")
        
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

class SubmitPaidLeaveTool(BaseTool):
    """
    有給休暇申請を提出します。
    """
    
    name: ClassVar[str] = "submit_paid_leave"
    description: ClassVar[str] = "有給休暇申請を提出します。"

    update_paid_leave_tool: Optional[UpdatePaidLeaveTool] = None

    def __init__(self, config: Config, client: WebClient, message: dict[str, Any]):
        super().__init__()
        self.update_paid_leave_tool = UpdatePaidLeaveTool(config, client, message)

    def _run(self, 
             user_name: str, 
             update_year: int | None, 
             update_month: int, 
             paid_leave_file_name: str) -> str:
        """
        有休休暇申請を提出する
        
        Args:
            user_name (str): 提出する従業員名
            update_year (int | None): 提出対象年。Noneの場合は自動的に決定されます
            update_month (int): 提出対象月
            paid_leave_file_name (str): 提出する有給休暇申請のファイル名
        """
        return self.update_paid_leave_tool._run(
            user_name, update_year, update_month, paid_leave_file_name
        )
