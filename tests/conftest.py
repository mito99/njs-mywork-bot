from pathlib import Path

import pytest

from bot.config import Config


@pytest.fixture
def test_config():
    """テスト用の設定を提供します。"""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_app_token="xapp-test-token",
        slack_signing_secret="test-secret",
        storage_path=Path("./test_storage"),
    )
