"""
使用方法を表示するコマンド
"""
from bot.commands.base import WorkCommand
from bot.config import Config
from bot.tools.work_tools.types import FileType


class UsageCommand(WorkCommand):
    """使用方法を表示するコマンド"""

    def __init__(self, config: Config):
        self.config = config

    async def execute(self, client, message, say):
        """使用方法を表示します。"""
        usage_message = (
            "使用可能なコマンド:\n"
            "- `cmd get <ストレージ名> <ファイル名>`: ファイルを取得\n"
            "- `cmd put <ストレージ名>`: ファイルをアップロード\n"
            "- `cmd list <ストレージ名>`: ファイル一覧を表示\n"
            "- `cmd delete <ストレージ名> <ファイル名>`: ファイルを削除\n"
            "- `cmd update 勤怠 <ファイル名>`: 勤怠表を更新\n"
            "- `cmd update 有休 <ファイル名>`: 有給休暇ファイルを更新\n\n"
            "利用可能なストレージ名:\n"
            + "\n".join([f"- {storage.value}" for storage in FileType])
        )
        await say(f"使用方法:\n{usage_message}") 