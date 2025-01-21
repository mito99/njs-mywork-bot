import logging
import os
from typing import Any, ClassVar, Optional

import requests
from langchain_core.tools import BaseTool

from bot.config import Config

from .types import FileType

logger = logging.getLogger(__name__)

class ReceiveFileTool(BaseTool):
    name: ClassVar[str] = "receive_file"
    description: ClassVar[str] = "ファイルを受信します"

    config: Optional[Config] = None
    message: Optional[dict[str, Any]] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, file_type: FileType, file_url: str, file_name: str):
        """
        Slackからファイルを受信し、指定されたストレージディレクトリに保存します。

        Args:
            file_type (FileType): 保存するファイルの種類（ストレージカテゴリ）
            file_url (str): Slackから取得したファイルのURL
            file_name (str): 保存するファイルの名前

        Returns:
            str: 保存されたファイルのパス

        Raises:
            ValueError: ファイルのURLまたはファイル名が取得できない場合
            requests.RequestException: ファイルのダウンロードに失敗した場合
            IOError: ファイルの保存に失敗した場合

        Note:
            - Slackのボットトークンを使用してファイルをダウンロードします。
            - ファイルは指定されたストレージディレクトリに保存されます。
        """
        logger.info(f"ReceiveFileTool: {file_type}, {file_url}, {file_name}")
        
        if not file_url:
            raise ValueError("ファイルのURLが取得できません。")

        if not file_name:
            raise ValueError("ファイル名が取得できません。")

        dir_path = self.config.application.storage[file_type].path
        save_path = os.path.join(dir_path, file_name)

        headers = {"Authorization": f"Bearer {self.config.slack_bot_task.bot_token}"}
        response = requests.get(file_url, headers=headers)
        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path 