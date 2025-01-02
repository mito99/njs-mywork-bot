import pytest
from slack_bolt import App

from bot.handlers.file_handler import register_file_handlers
from bot.handlers.message_handler import register_message_handlers


def test_message_handler_registration():
    """メッセージハンドラーの登録テスト"""
    app = App(token="xoxb-test-token")
    register_message_handlers(app)
    # ハンドラーが正しく登録されているか確認
    assert len(app._message_listeners) > 0


def test_file_handler_registration():
    """ファイルハンドラーの登録テスト"""
    app = App(token="xoxb-test-token")
    register_file_handlers(app)
    # ハンドラーが正しく登録されているか確認
    assert len(app._event_listeners) > 0
