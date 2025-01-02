import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.config import Config, load_config


def test_config_default_values():
    """デフォルト値の検証"""
    config = Config(
        slack_bot_token="test-bot-token",
        slack_app_token="test-app-token",
        slack_signing_secret="test-signing-secret",
        google_gemini_model_name="test-model",
    )
    assert config.log_level == "INFO"
    assert isinstance(config.startup_time, float)
    assert isinstance(config.slack, dict)
    assert isinstance(config.storage, dict)
    assert config.slack.get("allowed_user") == []


def test_config_validation_slack():
    """Slack設定のバリデーション検証"""
    with pytest.raises(ValueError):
        Config(
            slack_bot_token="test-bot-token",
            slack_app_token="test-app-token",
            slack_signing_secret="test-signing-secret",
            google_gemini_model_name="test-model",
            slack="invalid",  # 辞書ではない値を設定
        )


def test_config_validation_storage():
    """ストレージ設定のバリデーション検証"""
    with pytest.raises(ValueError):
        Config(
            slack_bot_token="test-bot-token",
            slack_app_token="test-app-token",
            slack_signing_secret="test-signing-secret",
            google_gemini_model_name="test-model",
            storage="invalid",  # 辞書ではない値を設定
        )


def test_config_custom_values():
    """カスタム値の設定検証"""
    custom_slack = {
        "allowed_user": ["user1", "user2"],
        "channels": {"general": "C123456"},
    }
    custom_storage = {"local": {"type": "local", "path": "/tmp/storage"}}

    config = Config(
        slack_bot_token="test-bot-token",
        slack_app_token="test-app-token",
        slack_signing_secret="test-signing-secret",
        google_gemini_model_name="test-model",
        slack=custom_slack,
        storage=custom_storage,
        log_level="DEBUG",
    )

    assert config.slack == custom_slack
    assert config.storage == custom_storage
    assert config.log_level == "DEBUG"


def test_required_fields():
    """必須フィールドの検証"""
    with pytest.raises(ValidationError):
        Config(
            slack_bot_token=None,
            slack_app_token=None,
            slack_signing_secret=None,
            google_gemini_model_name=None,
        )
