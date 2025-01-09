from enum import Enum


class FileType(str, Enum):
    ATTENDANCE = "勤怠"
    HOLIDAY = "有休" 
    BACKUP = "BACKUP"
    LOG = "LOG"