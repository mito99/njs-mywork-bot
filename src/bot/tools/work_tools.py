from typing import Any, ClassVar, Optional
import subprocess
from langchain_core.tools import BaseTool
from pydantic import Field
from slack_bolt import Say
from slack_sdk import WebClient

from bot.config import Config

class CreateAttendanceSheetTool(BaseTool):
    name: ClassVar[str] = "create_attendance_sheet"
    description: ClassVar[str] = "勤怠表を新規作成します"

    def _run(self) -> str:
        """
        新しい勤怠表を作成し、そのファイルパスを返します。

        Returns:
            str: 作成された勤怠表のファイルパス
        """
        return "storage/local/kintai.md"

class GetAttendanceSheetTool(BaseTool):
    name: ClassVar[str] = "get_attendance_sheet"
    description: ClassVar[str] = "最新の勤怠表のパスを取得します"

    def _run(self) -> str:
        """
        最新の勤怠表のファイルパスを取得します。

        Returns:
            str: 最新の勤怠表のファイルパス
        """
        return "storage/local/kintai.md"

class SendFileTool(BaseTool):
    name: ClassVar[str] = "send_file"
    description: ClassVar[str] = "指定されたファイルを送信します。"

    config: Optional[Config] = None
    client: Optional[WebClient] = None
    message: Optional[dict[str, Any]] = None
    say: Optional[Say] = None

    def __init__(
        self, 
        config: Optional[Config] = None, 
        client: Optional[WebClient] = None, 
        message: Optional[dict[str, Any]] = None, 
        say: Optional[Say] = None
    ):
        super().__init__()
        self.config = config
        self.client = client
        self.message = message
        self.say = say

    def _run(self, file_path: str):
        """
        指定されたファイルをSlackチャンネルに送信します。

        Args:
            file_path (str): 送信するファイルのパス

        Raises:
            ValueError: Slackクライアントまたはメッセージが設定されていない場合
        """
        if not self.client or not self.message:
            raise ValueError("Slack client or message is not configured")
        
        self.client.files_upload_v2(
            channel=self.message["channel"],
            file=file_path,
            initial_comment="勤怠表を送ります。",
        )

class ListAttendanceSheetsTool(BaseTool):
    name: ClassVar[str] = "list_attendance_sheets"
    description: ClassVar[str] = "勤怠表の一覧を取得します"

    def _run(self) -> list[str]:
        """
        ローカルの勤怠表ディレクトリにあるファイルの一覧を取得します。

        Returns:
            list[str]: 勤怠表ファイルのパスのリスト。
                       ディレクトリが存在しない、またはエラーが発生した場合は空のリストを返します。
        """
        result = subprocess.run(
            "ls storage/local/kintai/*",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().split("\n")
