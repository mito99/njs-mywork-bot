import logging
import os
import tempfile
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Optional

import requests
from langchain_core.tools import BaseTool
from njs_mywork_tools.attendance.models import Employee
from njs_mywork_tools.attendance.reader import GoogleTimeCardReader
from njs_mywork_tools.attendance.writer import ExcelWriter
from pydantic import Field
from slack_sdk import WebClient

from bot.config import Config

logger = logging.getLogger(__name__)

class FileType(str, Enum):
    ATTENDANCE = "勤怠"
    HOLIDAY = "有休"

class CreateAttendanceSheetTool(BaseTool):
    name: ClassVar[str] = "create_attendance_sheet"
    description: ClassVar[str] = "勤怠表を新規作成します"
    
    config: Optional[Config] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, 
             user_name: str, 
             output_year: int | None, 
             output_month: int, 
             attendance_file_name: str
    ) -> str:
        """
        指定されたユーザーの勤怠表を作成します。

        Args:
            user_name (str): ユーザフルネーム(例: 山田 太郎)
            output_year (int|None): 出力年 (例: 2025)。
            output_month (int): 出力月 (例: 1)
            attendance_file_name (str): 勤怠表ファイル名

        Returns:
            str: 作成された勤怠表ファイルのパス
        """
        
        # 出力年と出力月がfloatの場合があるのでintに変換
        output_year = int(output_year) if output_year else None
        output_month = int(output_month)
        
        time_card_reader = GoogleTimeCardReader(
            credentials_path=self.config.google_sheet.credentials_path,
            spreadsheet_key=self.config.google_sheet.spreadsheet_key,
            ssl_certificate_validation=self.config.google_sheet.ssl_certificate_validation,
        )
        
        # 出力月が現在の月より小さい場合は、前年を出力年とする
        # 出力月が現在の月より大きい場合は、当年を出力年とする
        if output_year is None:
            if datetime.now().month < output_month:
                output_year = datetime.now().year - 1
            else:
                output_year = datetime.now().year
        
        # 勤怠の範囲は前月21日から当月20日まで
        start_date = datetime(output_year, (output_month - 1) % 12 + 1, 21).date()
        end_date = datetime(output_year, output_month, 20).date()
        
        # 勤怠データを取得
        try:
            timecard_data_list = time_card_reader.read_timecard_sheet(start_date, end_date)
        except Exception as e:
            logger.error(f"勤怠データの取得に失敗しました。エラー: {e}")
            raise ValueError(f"勤怠データの取得に失敗しました。エラー: {e}")
        
        # 勤怠表ファイルを作成
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
        """
        指定されたファイルをSlackチャンネルに送信します。

        Args:
            file_name (str): 送信するファイル名
            file_type (FileType): ファイルの種類を示す列挙型

        Raises:
            ValueError: Slackクライアントまたはメッセージが設定されていない場合
        """
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

class ReceiveFileTool(BaseTool):
    name: ClassVar[str] = "receive_file"
    description: ClassVar[str] = "ファイルを受信します"

    config: Optional[Config] = None
    message: Optional[dict[str, Any]] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, file_type: FileType, file_url: str, file_name: str):
        """
        Slackから指定されたファイルを受信し、指定されたストレージディレクトリに保存します。

        Args:
            file_type (FileType): ファイルの種類を示す列挙型
            file_url (str): ファイルのダウンロードURL
            file_name (str): 保存するファイル名

        Returns:
            str: 保存されたファイルの完全パス

        Raises:
            ValueError: 以下の場合に発生
                - file_urlが空の場合
                - file_nameが空の場合
                - ファイルのダウンロードに失敗した場合
        """
        if not file_url:
            raise ValueError("ファイルのURLが取得できません。")

        if not file_name:
            raise ValueError("ファイル名が取得できません。")

        dir_path = self.config.application.storage[file_type].path
        save_path = os.path.join(dir_path, file_name)

        headers = {"Authorization": f"Bearer {self.config.slack_bot_token}"}
        response = requests.get(file_url, headers=headers)
        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path
class ListFilesTool(BaseTool):
    name: ClassVar[str] = "list_files"
    description: ClassVar[str] = "ファイルの一覧を取得します"

    config: Optional[Config] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, file_type: FileType) -> list[str]:
        """
        指定されたファイルタイプのディレクトリ内のファイル一覧を取得します。

        Args:
            file_type (FileType): 取得するファイルの種類を指定する列挙型

        Returns:
            list[str]: ファイル名のリスト。
                       ディレクトリが存在しない、またはコマンド実行に失敗した場合は空のリストを返します。

        Note:
            - lsコマンドを使用してファイル一覧を取得します。
            - サブディレクトリ内のファイルは含まれません。
        """
        dir_path = self.config.application.storage[file_type].path
        try:
            files = os.listdir(dir_path)
            # ディレクトリ内のファイルのみを取得
            files = [f for f in files if os.path.isfile(os.path.join(dir_path, f))]
            return files
        except OSError:
            return []

class DeleteStorageFileTool(BaseTool):
    name: ClassVar[str] = "delete_storage_file"
    description: ClassVar[str] = "指定されたファイルをストレージから削除します"

    config: Optional[Config] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, file_name: str, file_type: FileType) -> str:
        """
        指定されたファイルをストレージから削除します。

        Args:
            file_name (str): 削除するファイル名
            file_type (FileType): ファイルの種類を示す列挙型

        Returns:
            str: 削除されたファイルのパス

        Raises:
            ValueError: 以下の場合に発生
                - ファイルが存在しない
                - ファイルの削除に失敗した
        """
        dir_path = self.config.application.storage[file_type].path
        file_path = os.path.join(dir_path, file_name)

        if not os.path.exists(file_path):
            raise ValueError(f"ファイルが見つかりません: {file_path}")

        try:
            os.remove(file_path)
            return file_path
        except Exception as e:
            logger.error(f"ファイルの削除に失敗しました。エラー: {e}")
            raise ValueError(f"ファイルの削除に失敗しました。エラー: {e}")