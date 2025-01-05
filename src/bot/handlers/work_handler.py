import logging
import re
from pathlib import Path
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from slack_bolt import App, Say
from slack_sdk import WebClient
from bot.config import Config
from bot.handlers.validation import is_valid_message
from bot.services.chatbot.work_chatbot import WorkChatbot
from bot.commands.work_commands import UsageCommand, WorkCommand
from bot.tools.work_tools import (
    CreateAttendanceSheetTool,
    ListFilesTool,
    SendFileTool,
)
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def register_work_handlers(app: App, config: Config):
    """メッセージ関連のイベントハンドラーを登録します。"""

    llm = ChatGoogleGenerativeAI(
        model=config.google_gemini_model_name,
    )

    @app.message(re.compile("^cmd\s+.*"))
    def handle_command(message, say, client):
        """コマンドの処理"""

        # メッセージの検証を行う
        if not is_valid_message(message, config):
            say("メッセージが許可されていません。")
            return

        # メッセージテキストを取得
        text = message.get("text", "").strip()
        command = WorkCommand.create(text, config)
        if command is UsageCommand:
            command.execute(client, message, say)
            return

        try:
            command.execute(client, message, say)
        except Exception as e:
            say(f"エラーが発生しました。\n{e}")
            return

    def _get_thread_history(client: WebClient, channel: str, thread_ts: str, limit: int = 10) -> list[dict[str, str]]:
        """スレッドの履歴を取得する

        Args:
            client (WebClient): Slackクライアント
            channel (str): チャンネルID
            thread_ts (str): スレッドのタイムスタンプ
            limit (int, optional): 取得するメッセージの上限. デフォルトは10.

        Returns:
            list[dict[str, str]]: メッセージ情報のリスト。各メッセージは以下の形式:
                {
                    "text": メッセージテキスト,
                    "role": "assistant" または "user",
                    "name": 発言者の表示名
                }
        """
        try:
            thread_messages = client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=limit
            )
            messages = []
            for msg in thread_messages["messages"]:
                # ボットの発言かどうかを判定
                is_bot = msg.get("bot_id") is not None
                
                # ユーザー情報を取得（ボットでない場合）
                display_name = ""
                if not is_bot:
                    user_info = client.users_info(user=msg["user"])
                    display_name = user_info["user"]["profile"]["display_name"]

                messages.append({
                    "text": msg["text"],
                    "role": "assistant" if is_bot else "user",
                    "name": display_name if not is_bot else "AI"
                })
            return messages
        except Exception as e:
            logger.error(f"スレッド履歴の取得に失敗しました: {e}")
            return []

    @app.message(re.compile("^(?!cmd).*"))
    def handle_chatbot(message: dict[str, Any], say: Say, client: WebClient):
        """チャットボットの処理"""

        user_id = message["user"]
        user_info = client.users_info(user=user_id)
        display_name = user_info["user"]["profile"]["display_name"]
        message_text = message["text"]

        # スレッドのタイムスタンプを取得
        thread_ts = message.get("thread_ts", message["ts"])
        
        # スレッドの履歴を取得
        history = _get_thread_history(
            client=client,
            channel=message["channel"],
            thread_ts=thread_ts,
            limit=10
        )

        # 初回メッセージの送信
        initial_response = client.chat_postMessage(
            channel=message["channel"],
            text=f"...",
            thread_ts=thread_ts,
        )

        chatbot = WorkChatbot(config, llm)
        chatbot.add_tool(CreateAttendanceSheetTool())
        chatbot.add_tool(SendFileTool(config, client, message, say))
        chatbot.add_tool(ListFilesTool(config))

        # ストリーミングで返答を送信
        for chunk in chatbot.stream_chat(
            message_text, display_name, thread_ts, history):
            client.chat_update(
                channel=message["channel"],
                ts=initial_response["ts"],
                text=chunk,
            )
