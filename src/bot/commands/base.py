"""
作業コマンドの基底クラスとビルダー
"""
import logging
from abc import ABC, abstractmethod

from bot.config import Config
from bot.tools.work_tools.types import FileType

logger = logging.getLogger(__name__)


class WorkCommand(ABC):
    """作業コマンドの抽象基底クラス"""

    @abstractmethod
    async def execute(self, client, message, say):
        """コマンドを実行する抽象メソッド"""
        pass

    @classmethod
    async def create(cls, command_text: str, config: Config) -> "WorkCommand":
        """コマンドに応じたコマンドを返すビルダーメソッド"""
        from bot.commands.delete import DeleteFileCommand
        from bot.commands.get import GetFileCommand
        from bot.commands.list import ListFileCommand
        from bot.commands.put import PutFileCommand
        from bot.commands.update_attendance import UpdateAttendanceCommand
        from bot.commands.update_paid_leave import UpdatePaidLeaveCommand
        from bot.commands.usage import UsageCommand

        # コマンドテキストをスペースで分割
        parts = command_text.split()
        action = parts[0].upper() if len(parts) > 0 else None
        file_type = parts[1] if len(parts) > 1 else None
        file_name = parts[2] if len(parts) > 2 else None

        storage_types = list(config.application.storage.keys())
        if file_type not in storage_types:
            return UsageCommand(config)

        if action == "GET":
            if not file_name:
                return UsageCommand(config)
            return GetFileCommand(file_type, file_name, config)
        elif action == "LIST":
            return ListFileCommand(file_type, config)
        elif action == "PUT":
            return PutFileCommand(file_type, config)
        elif action == "DELETE":
            return DeleteFileCommand(file_type, file_name, config)
        elif action == "UPDATE":
            if not file_name:
                return UsageCommand(config)
            if file_type == FileType.ATTENDANCE.value:
                return UpdateAttendanceCommand(file_type, file_name, config)
            elif file_type == FileType.HOLIDAY.value:
                return UpdatePaidLeaveCommand(file_type, file_name, config)

        return UsageCommand(config) 