import logging
from typing import Iterator

from pydantic import BaseModel, Field

from bot.config import Config, load_config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from bot.tools.work_tools import (
    CreateAttendanceSheetTool,
    ListFilesTool,
    SendFileTool,
)
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)
class WorkAgentState(BaseModel):
    """エージェントの状態"""

    user_name: str = Field(default="作業を依頼したユーザ名")
    user_query: str = Field(default="依頼された作業内容")
    user_history: list[dict] = Field(default="ユーザのメッセージ履歴")

class WorkAgent:
    """ワークチャットボットのエージェント"""

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
            "- 8. ユーザがファイルを要求した場合ファイルパスを含めツールを呼び出してください。"
        )

    def add_tool(self, tool: BaseTool):
        self.tools.append(tool)

    def invoke(self, state: WorkAgentState, config: dict) -> Iterator[str]:
        # ユーザのメッセージ履歴を取得
        user_history = state.user_history

        agent = create_react_agent(
            self.llm,
            self.tools,
        )

        str_user_history = "\n".join([f"{message['role']}: {message['text']}" for message in user_history])

        # ユーザメッセージを追加
        user_message = HumanMessage(
            f"ユーザ名: {state.user_name}\n"
            f"ユーザの依頼内容:\n{state.user_query}\n\n"
            f"ユーザのメッセージ履歴:\n{str_user_history}"
        )
        messages = [self.system_message, user_message]

        stream = agent.stream(
            {"messages": messages}, 
            config=config
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

class WorkChatbot:
    """ワークチャットボットのサービス"""

    def __init__(self, config: Config, llm: BaseChatModel):
        self.config = config
        self.agent = WorkAgent(llm)

    def add_tool(self, tool: BaseTool):
        self.agent.add_tool(tool)

    def stream_chat(
        self,
        message: str,
        user_name: str,
        thread_ts: str,
        user_history: list[dict],
    ) -> Iterator[str]:
        """チャットボットにメッセージを送信し、ストリーミング形式で返答を返します。"""
        state = WorkAgentState(user_name=user_name, user_query=message, user_history=user_history)
        config = {
            "configurable": {
                "thread_id": thread_ts,
            }
        }
        return self.agent.invoke(state, config)

if __name__ == "__main__":
    config = load_config()
    llm = ChatGoogleGenerativeAI(
        model=config.google_gemini_model_name,
    )
    chatbot = WorkChatbot(config, llm)
    chatbot.add_tool(CreateAttendanceSheetTool())
    chatbot.add_tool(SendFileTool())
    chatbot.add_tool(ListFilesTool())
    for response in chatbot.chat("僕の勤怠表送って", "やまだ"):
        print(response)