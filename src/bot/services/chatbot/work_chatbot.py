import logging
from typing import Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AttachedFile(BaseModel):
    file_name: str = Field(default="添付ファイル名")
    file_url: str = Field(default="添付ファイルURL")
    file_id: str = Field(default="添付ファイルID")

class ChatMessage(BaseModel):
    role: str = Field(..., description="メッセージ送信者")
    name: str = Field(..., description="メッセージ送信者")
    message: str = Field(..., description="メッセージ内容") 
    attached_files: list[AttachedFile] = Field(default_factory=list, description="添付ファイル情報")

class WorkChatbot:
    """ワークチャットボット"""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.tools = []
        self.system_message = SystemMessage(
            "あなたは会社内部で働くフレンドリーな友達です。\n"
            "会社外部で働くユーザのために依頼された作業をルールに従って行なってください。\n"
            "ルール:\n"
            "- 1. ユーザの依頼内容に応じて、ツールを使用して作業を行なってください。\n"
            "- 2. 基本的に挨拶は不要です。\n"
            "- 3. ユーザからの要求が理解できない場合、ユーザに質問をしてください。\n"
            "- 4. 作業前に応答を返し、その後作業に入ってください。\n"
            "- 5. 作業進捗を事細かくユーザに伝えてください。\n"
            "- 6. 作業完了後は**必ず**結果をユーザに伝えて締めくくってください。\n"
            "- 7. ツール実行結果がエラーの場合は、正常に実行できなかった旨のメッセージを返却してください。\n"
            "- 8. ユーザがファイルを要求した場合ファイルパスを含めツールを呼び出してください。\n"
            "- 9. エラー発生時は再度実行する必要はありません。エラーをユーザに通知してください。\n"
            "ツールについて:\n"
            "- 1. 勤怠表更新ツール: \n"
            "    a. ユーザが更新対象年を指定しない場合、更新対象年はNoneとしてツールを呼び出してください。\n"
            "    b. 勤怠表ファイル名は、ファイル一覧ツールを使用して取得してください。\n"
            "       ファイル名が一つに絞れた場合は、そのファイル名でツールを呼び出してください。**ユーザの確認は不要**\n"
            "       ファイル名が複数に絞れた場合は、絞り込んだファイル名をユーザに提示し指定してもらってください。\n"
        )

    def add_tool(self, tool: BaseTool):
        self.tools.append(tool)

    def stream_chat(self, message: ChatMessage, history: list[ChatMessage], thread_ts: str) -> Iterator[str]:
        # ユーザのメッセージ履歴を取得
        agent = create_react_agent(
            self.llm,
            self.tools,
        )
        
        str_attached_files = "\n".join(
            [ 
                f" - {file.model_dump_json()}" 
                for file in message.attached_files
            ]
        )
        str_user_history = "\n".join(
            [
                f" - {msg.model_dump_json()}" 
                for msg in history
            ]
        )

        # ユーザメッセージを追加
        user_message = HumanMessage(
            f"ユーザ名: {message.name}\n"
            f"ユーザの依頼内容:\n{message.message}\n\n"
            f"ユーザの添付ファイル:\n{str_attached_files}\n\n"
            f"ユーザとのメッセージ履歴:\n{str_user_history}"
        )
        messages = [self.system_message, user_message]

        stream = agent.stream(
            {"messages": messages}, 
            config={
                "thread_ts": thread_ts
            }
        )

        for chunk in stream:
            # ツール実行結果のログ出力
            if chunk.get("tools"):
                logger.debug(f"ツール実行結果: {chunk.get('tools')}")
                continue

            # エージェントの応答がない場合はスキップ
            agent_response = chunk.get("agent")
            if not agent_response:
                continue

            # メッセージがない場合はスキップ
            messages = agent_response.get("messages", [])
            if not messages:
                continue

            # 最初のメッセージを取得
            ai_message = messages[0]
            if not ai_message.content:
                continue

            # メッセージの種類に応じて処理
            content = ai_message.content
            if isinstance(content, str):
                yield content
            elif isinstance(content, list):
                yield "\n".join(content)