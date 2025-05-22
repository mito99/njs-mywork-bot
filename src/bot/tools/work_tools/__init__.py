import os
import shutil

from bot.config import load_config

from .attendance import SubmitAttendanceSheetTool, UpdateAttendanceSheetTool
from .datetime_tool import GetCurrentDateTimeTool
from .file_deleter import DeleteStorageFileTool
from .file_lister import ListFilesTool
from .file_receiver import ReceiveFileTool
from .file_sender import SendFileTool
from .paid_leave import SubmitPaidLeaveTool, UpdatePaidLeaveTool
from .types import FileType

__all__ = [
    'FileType',
    'UpdateAttendanceSheetTool',
    'SendFileTool',
    'ReceiveFileTool',
    'ListFilesTool',
    'DeleteStorageFileTool',
    'SubmitAttendanceSheetTool',
    'GetCurrentDateTimeTool',
    'UpdatePaidLeaveTool',
    'SubmitPaidLeaveTool',
    'GetAttendanceStatusTool',
] 

config = load_config()

def backup_file(file_path: str):
    backup_dir_path = config.application.storage[FileType.BACKUP].path
    shutil.copy(file_path, backup_dir_path)
