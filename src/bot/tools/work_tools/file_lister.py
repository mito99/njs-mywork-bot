import logging
import os
from typing import ClassVar, Optional

from langchain_core.tools import BaseTool

from bot.config import Config

from .types import FileType

logger = logging.getLogger(__name__)

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
            file_type (FileType): 一覧を取得するファイルの種類（ストレージカテゴリ）

        Returns:
            list[str]: ディレクトリ内のファイル名のリスト。
                       ディレクトリが存在しない、またはアクセスできない場合は空のリストを返します。

        Note:
            - ディレクトリ内のファイルのみを返し、サブディレクトリは除外します。
            - ファイルの取得中にエラーが発生した場合は空のリストを返します。
        """
        logger.info(f"ListFilesTool: {file_type}")
        
        dir_path = self.config.application.storage[file_type].path
        try:
            files = os.listdir(dir_path)
            # ディレクトリ内のファイルのみを取得
            files = [f for f in files if os.path.isfile(os.path.join(dir_path, f))]
            return files
        except OSError:
            return [] 