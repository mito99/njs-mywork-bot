import subprocess
from typing import Any
from langchain_core.tools import tool

def create_attendance_sheet() -> str:
    """勤怠表を作成する

    Returns:
        str: 作成された勤怠表のファイルパス
    """
    return "storage/local/kintai.md"

def get_attendance_sheet() -> str:
    """最新の勤怠表のパスを取得する

    Returns:
        str: 最新の勤怠表のファイルパス
    """
    return "storage/local/kintai.md"

def send_file(file_path: str) -> str:
    """指定されたファイルを送信する

    Args:
        file_path (str): 送信するファイルのパス

    Returns:
        str: ファイル送信結果
    """
    subprocess.run(f"cp {file_path} storage/remote/kintai.md", shell=True)
    return f"File {file_path} has been sent" 

def list_attendance_sheets() -> list[str]:
    """勤怠表の一覧を取得する

    Returns:
        list[str]: 勤怠表のファイルパス一覧
    """
    # storage/local 配下の勤怠ファイルを取得
    result = subprocess.run(
        "ls storage/local/kintai/*",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []
    return result.stdout.strip().split("\n")
