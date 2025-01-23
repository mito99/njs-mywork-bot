import logging
import os
from pathlib import Path
from typing import ClassVar, Optional

from langchain_core.tools import BaseTool
from tenacity import retry, stop_after_attempt, wait_exponential

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

    @retry(
        stop=stop_after_attempt(3),  # 最大3回リトライ
        wait=wait_exponential(multiplier=1, min=4, max=10)  # 指数バックオフ
    )
    def _run(self, file_type: FileType) -> list[str]:
        """
        指定されたファイルタイプのディレクトリ内のファイル名一覧を取得します。
        
        リトライ機能付きで、ネットワーク上のファイル取得を安定化させます。
        """
        logger.info(f"ListFilesTool: {file_type}")
        
        dir_path = self.config.application.storage[file_type].path
        try:
            files = list(Path(dir_path).glob("*"))  # イテレータを即座にリストに変換
            if not files:
                logger.warning(f"ディレクトリ {dir_path} にファイルが見つかりません")
                return []
                
            # ディレクトリ内のファイルのみを取得し、ファイル名に変換
            file_names = [f.name for f in files if f.is_file()]
            logger.info(f"取得したファイル数: {len(file_names)}")
            return file_names
            
        except OSError as e:
            logger.error(f"ファイル一覧の取得に失敗: {e}")
            raise  # リトライのために例外を再送出 