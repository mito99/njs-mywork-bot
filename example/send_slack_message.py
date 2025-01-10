#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .envファイルから環境変数を読み込む
load_dotenv()

# logging.basicConfig(level=logging.DEBUG)

# Slack Boltアプリケーションを初期化
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def send_dm_to_user(user_id: str, text: str) -> None:
    try:
        response = app.client.conversations_open(users=user_id)
        print(f"conversations.open response: {response}")
        channel_id = response["channel"]["id"]
        result = app.client.chat_postMessage(channel=channel_id, text=text)
        print(f"Message sent: {result}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # 環境変数のチェック
    if not os.environ.get("SLACK_BOT_TOKEN") or not os.environ.get("SLACK_APP_TOKEN"):
        print("環境変数 SLACK_BOT_TOKEN と SLACK_APP_TOKEN を設定してください。")
        return

    # テスト用のメッセージを送信
    user_id = "U085CTDATNJ"
    message = "メールが届いていますよ！"
    send_dm_to_user(user_id, message)

if __name__ == "__main__":
    main() 