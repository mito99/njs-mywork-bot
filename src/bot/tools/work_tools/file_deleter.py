import logging
import os
from typing import ClassVar, Optional

from langchain_core.tools import BaseTool

from bot.config import Config

from .types import FileType

logger = logging.getLogger(__name__)

class DeleteStorageFileTool(BaseTool):
    name: ClassVar[str] = "delete_storage_file"
    description: ClassVar[str] = "指定されたファイルをストレージから削除します"

    config: Optional[Config] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, file_name: str, file_type: FileType) -> str:
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