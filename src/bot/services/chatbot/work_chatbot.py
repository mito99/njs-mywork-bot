import logging
from typing import AsyncIterator, Iterator

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
            "あなたは会社内部で働く効率的なアシスタントです。\n"
            "会社外部で働くユーザのために依頼された作業を直接的かつ簡潔に行ってください。\n"
            "ユーザの依頼内容に応じて、ツールを使用して作業を行なってください。\n\n"
            "作業ごとにこれから何をするかを都度ユーザに伝えてください。\n"
            "# 代表的な依頼と対応方法 \n"
            "1. 勤怠ファイル/有休ファイルの更新依頼\n"
            "  - 更新依頼があった場合、list_filesツールを使用し、依頼したユーザ名に該当するファイルを特定してください。\n"
            "  - 依頼内容に更新対象年月が指定されなかった場合は、get_current_datetimeツールを使用し、"
            "    現在の年月を取得し、これを更新対象年月としてください。\n"
            "  - 続いて、特定したファイルを勤怠ファイルの場合はupdate_attendance_sheetツール、"
            "    有休ファイルの場合はupdate_paid_leaveツールを使用し、ファイルを更新してください。\n"
            "  - 更新後、send_fileツールを使用し、更新後のファイルを提出してください。\n"
            "2. 勤務時間の推測依頼\n"
            "  - 勤務時間の推測依頼があった場合、get_attendance_statusツールを使用し、勤怠データを取得してください。\n"
            "  - 依頼内容に推測対象年月が指定されなかった場合は、get_current_datetimeツールを使用し、"
            "    現在の年月を取得し、これを推測対象年月としてください。\n"
            "  - 続いて、月末までの勤務時間を求めますが、入力されていない勤務時間を過去のデータから推測して求めユーザに伝えてください。\n"
            "  - 依頼内容に、推測に対してリクエストが含まれている場合、推測内容にリクエスト内容を加味してください。\n"
            "  - リクエスト例:\n"
            "    - リクエスト: 仕事が忙しくなりそう => 過去データを参考に、入力されてない勤務時間は、増やした推測値とする。\n"
            "    - リクエスト: 休みを2日取る予定 => 推測する勤務時間の中から、平日の中から２日分を休みとして推測する。\n"
            "    - リクエスト: 全部定時でお願い => 推測する勤務時間を全て定時勤務(08:50～17:30 - 07:45)とする。\n"
            "  - 回答は次の形式で行ってください。\n"
            "    * 05/09(金) - 出勤 - 08:50～18:40 - 08:50\n"
            "    * 05/10(土) - 休日 - 00:00～00:00 - 00:00\n"
            "    * 05/11(日) - 休日 - 00:00～00:00 - 00:00\n"
            "    * 05/12(月) - 出勤 - 08:50～18:40 - 08:50 [推測]\n"
            "    -------------------------------------------------\n"
            "    * 勤務時間計: xx時間xx分\n"

        )

    def add_tool(self, tool: BaseTool):
        self.tools.append(tool)

    async def stream_chat(self, message: ChatMessage, history: list[ChatMessage], thread_ts: str) -> AsyncIterator[str]:
        # ユーザのメッセージ履歴を取得
        agent = create_react_agent(
            self.llm,
            self.tools,
        )
        
        resolved_attached_files = [file for file in message.attached_files]
        str_attached_files = "\n".join(
            [ 
                f" - {file.model_dump_json()}" 
                for file in resolved_attached_files
            ]
        )
        
        # 非同期で取得されたhistoryを同期的に処理するために修正
        resolved_history = [await hist for hist in history]
        str_user_history = "\n".join(
            [
                f" - {msg.model_dump_json()}" 
                for msg in resolved_history
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
            # ツール実行結果の処理
            if chunk.get("tools"):
                tool_results = chunk.get("tools")
                logger.debug(f"ツール実行結果: {tool_results}")
                continue

            # エージェントの応答がない場合はスキップ
            agent_response = chunk.get("agent")
            logger.debug(f"エージェントの応答: {agent_response}")
            if not agent_response:
                continue

            # メッセージがない場合はスキップ
            messages = agent_response.get("messages", [])
            logger.debug(f"メッセージ: {messages}")
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