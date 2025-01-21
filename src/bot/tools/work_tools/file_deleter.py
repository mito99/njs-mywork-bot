import logging
import os
from pathlib import Path
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
        """
        指定されたファイルをストレージから削除します。

        Args:
            file_name (str): 削除するファイルの名前
            file_type (FileType): 削除するファイルの種類（ストレージカテゴリ）

        Returns:
            str: 削除されたファイルのパス

        Raises:
            ValueError: ファイルが見つからない場合、または削除に失敗した場合
        """
        logger.info(f"DeleteStorageFileTool: {file_name}, {file_type}")
        
        dir_path = self.config.application.storage[file_type].path
        file_path = Path(dir_path) / file_name

        if not Path(file_path).exists():
            raise ValueError(f"ファイルが見つかりません: {file_path}")

        try:
            Path(file_path).unlink()
            return file_path
        except Exception as e:
            logger.error(f"ファイルの削除に失敗しました。エラー: {e}")
            raise ValueError(f"ファイルの削除に失敗しました。エラー: {e}") 