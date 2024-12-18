from pathlib import Path
from typing import BinaryIO


class FileStorage:
    """ファイル保存を管理するサービス"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_name: str, content: BinaryIO) -> Path:
        """ファイルを保存し、保存先のパスを返します。"""
        file_path = self.base_path / file_name
        with file_path.open("wb") as f:
            f.write(content.read())
        return file_path
