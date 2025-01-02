from io import BytesIO
from pathlib import Path

import pytest

from bot.services.storage import FileStorage


@pytest.fixture
def storage(tmp_path):
    """テスト用のストレージインスタンスを提供します。"""
    return FileStorage(tmp_path)


def test_file_storage_save(storage):
    """ファイル保存機能のテスト"""
    test_content = b"Hello, World!"
    file_content = BytesIO(test_content)

    saved_path = storage.save_file("test.txt", file_content)
    assert saved_path.exists()

    with saved_path.open("rb") as f:
        assert f.read() == test_content
