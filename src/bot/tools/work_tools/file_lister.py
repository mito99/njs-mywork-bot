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
        dir_path = self.config.application.storage[file_type].path
        try:
            files = os.listdir(dir_path)
            # ディレクトリ内のファイルのみを取得
            files = [f for f in files if os.path.isfile(os.path.join(dir_path, f))]
            return files
        except OSError:
            return [] 