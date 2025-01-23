import logging
import os
import socket
import time
from pathlib import Path
from typing import ClassVar, Optional

from langchain_core.tools import BaseTool

from bot.config import Config

from .types import FileType

logger = logging.getLogger(__name__)

class ListFilesTool(BaseTool):
    name: ClassVar[str] = "list_files"
    description: ClassVar[str] = "ファイルの一覧を取得します"

    config: Optional[Config] = None
    MAX_RETRIES: ClassVar[int] = 3
    RETRY_DELAY: ClassVar[float] = 1.0  # 秒
    TIMEOUT: ClassVar[float] = 5.0  # 秒

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, file_type: FileType) -> list[str]:
        """
        指定されたファイルタイプのディレクトリ内のファイル名一覧を取得します。

        Args:
            file_type (FileType): 一覧を取得するファイルの種類（ストレージカテゴリ）

        Returns:
            list[str]: ディレクトリ内のファイル名のリスト。
                       ディレクトリが存在しない、またはアクセスできない場合は空のリストを返します。

        Note:
            - ディレクトリ内のファイルのみを返し、サブディレクトリは除外します。
            - ファイルの取得中にエラーが発生した場合は空のリストを返します。
            - ネットワークエラーに対してリトライ機能を提供します。
        """
        logger.info(f"ListFilesTool: ファイル一覧取得開始 - {file_type}")
        
        dir_path = self.config.application.storage[file_type].path
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # タイムアウト付きでディレクトリ内のファイルを取得
                with socket.create_connection((Path(dir_path).parent, 0), timeout=self.TIMEOUT):
                    files = Path(dir_path).glob("*")
                    # ディレクトリ内のファイルのみを取得し、ファイル名に変換
                    files_list = [f.name for f in files if f.is_file()]
                    
                    logger.info(f"ListFilesTool: {file_type} - {len(files_list)}個のファイルを取得")
                    return files_list
            
            except (OSError, socket.error, socket.timeout) as e:
                logger.warning(f"ListFilesTool: ファイル一覧取得エラー - 試行 {attempt + 1}/{self.MAX_RETRIES} - {e}")
                
                # 最後の試行でない場合はリトライ
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"ListFilesTool: ファイル一覧取得に完全に失敗 - {dir_path}")
        
        return [] 