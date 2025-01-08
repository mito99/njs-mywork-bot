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
        if not file_url:
            raise ValueError("ファイルのURLが取得できません。")

        if not file_name:
            raise ValueError("ファイル名が取得できません。")

        dir_path = self.config.application.storage[file_type].path
        save_path = os.path.join(dir_path, file_name)

        headers = {"Authorization": f"Bearer {self.config.slack_bot_token}"}
        response = requests.get(file_url, headers=headers)
        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path 