import logging
import re
from pathlib import Path
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from slack_bolt import Say
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from bot.commands.base import WorkCommand
from bot.config import Config
from bot.handlers.validation import is_valid_message
from bot.services.chatbot.work_chatbot import (AttachedFile, ChatMessage,
                                               WorkChatbot)
from bot.tools.work_tools import (DeleteStorageFileTool,
                                  GetCurrentDateTimeTool, ListFilesTool,
                                  ReceiveFileTool, SendFileTool,
                                  SubmitAttendanceSheetTool,
                                  UpdateAttendanceSheetTool)
from bot.tools.work_tools.attendance import GetAttendanceStatusTool
from bot.tools.work_tools.paid_leave import (SubmitPaidLeaveTool,
                                             UpdatePaidLeaveTool)

logger = logging.getLogger(__name__)


def register_work_handlers(app: AsyncApp, config: Config):
    """メッセージ関連のイベントハンドラーを登録します。"""
    llm = ChatGoogleGenerativeAI(
        model=config.google_gemini_model_name,
        google_api_key=config.google_api_key,
    )
    
    @app.message(re.compile("^cmd\s+.*"))
    async def handle_command(message, say, client):
        """コマンドの処理"""

        # メッセージの検証を行う
        if not is_valid_message(message, config):
            await say("メッセージが許可されていません。")
            return

        # メッセージテキストを取得
        text = message.get("text", "").replace("cmd", "", 1).strip()
        try:
            command = await WorkCommand.create(text, config)
            await command.execute(client, message, say)
        except Exception as e:
            await say(f"エラーが発生しました。\n{e}")
            return

    @app.message(re.compile("^(?!cmd).*"))
    async def handle_chatbot(message: dict[str, Any], say: Say, client: AsyncWebClient):
        """チャットボットの処理"""

        # スレッドのタイムスタンプを取得
        thread_ts = message.get("thread_ts", message["ts"])
        
        # ユーザー情報を非同期で取得
        user_info = await client.users_info(user=message["user"])
        
        # 初回メッセージの送信を非同期で実行
        initial_response = await client.chat_postMessage(
            channel=message["channel"],
            text="...",
            thread_ts=thread_ts,
        )
        
        # 現在のメッセージをChatMessageに変換（非同期関数に変更）
        current_message = await _create_chat_message(message, client)
        chat_history = await _get_thread_history(client, message["channel"], thread_ts, limit=10)
        
        chatbot = WorkChatbot(llm)
        chatbot.add_tool(UpdateAttendanceSheetTool(config, client, message))
        chatbot.add_tool(UpdatePaidLeaveTool(config, client, message))
        chatbot.add_tool(SendFileTool(config, client, message))
        chatbot.add_tool(ListFilesTool(config))
        chatbot.add_tool(ReceiveFileTool(config))
        chatbot.add_tool(DeleteStorageFileTool(config))
        chatbot.add_tool(SubmitAttendanceSheetTool(config, client, message))
        chatbot.add_tool(SubmitPaidLeaveTool(config, client, message))
        chatbot.add_tool(GetCurrentDateTimeTool())
        chatbot.add_tool(GetAttendanceStatusTool(config, client, message))

        # 累積メッセージを保持する変数を追加
        accumulated_message = ""
        
        # ストリーミングで返答を送信（非同期で処理）
        async for chunk in chatbot.stream_chat(
            current_message, chat_history, thread_ts
        ):
            # チャンクを累積メッセージに追加
            accumulated_message += chunk
            
            await client.chat_update(
                channel=message["channel"],
                ts=initial_response["ts"],
                text=accumulated_message,  
            )

    @app.event({
        "type": "message",
        "subtype": ["message_changed", "message_deleted"]
    })
    async def handle_message_changed(body, logger):
        """
        メッセージが編集された際のイベントを処理します
        
        Args:
            body: イベントのペイロード
            logger: ロガーインスタンス
        """
        logger.debug(f"Message changed event received: {body}")
        # 必要に応じて追加の処理をここに実装

    async def _create_chat_message(message: dict, client: AsyncWebClient) -> ChatMessage:
        """SlackメッセージからChatMessageインスタンスを生成します。

        Args:
            message (dict): Slackメッセージオブジェクト
            client (AsyncWebClient): 非同期Slackクライアント

        Returns:
            ChatMessage: 生成されたChatMessageインスタンス
        """

        user_id = message["user"]
        # users_infoを非同期で取得
        user_info = await client.users_info(user=user_id)
        real_name = user_info["user"]["profile"]["real_name"]
        message_text = message["text"]

        role = "assistant" if message.get("bot_id") else "user"
        attached_files = [
            AttachedFile(
                file_name=file.get("name", ""),
                file_url=file.get("url_private_download", ""),
                file_id=file.get("id", "")
            )
            for file in message.get("files", [])
        ]

        return ChatMessage(
            role=role,
            name=real_name,
            message=message_text,
            attached_files=attached_files
        )

    async def _get_thread_history(client: AsyncWebClient, channel: str, thread_ts: str, limit: int = 10) -> list[ChatMessage]:
        """スレッドの履歴を取得する

        Args:
            client (AsyncWebClient): 非同期Slackクライアント
            channel (str): チャンネルID
            thread_ts (str): スレッドのタイムスタンプ
            limit (int, optional): 取得するメッセージの上限. デフォルトは10.

        Returns:
            list[ChatMessage]: ChatMessageオブジェクトのリスト
        """
        try:
            thread_messages = await client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=limit
            )
            thread_messages = thread_messages["messages"]
            return [_create_chat_message(msg, client) for msg in thread_messages]
        except Exception as e:
            logger.error(f"スレッド履歴の取得に失敗しました: {e}")
            return []