from pathlib import Path
from typing import Callable, Iterator

from pydantic import BaseModel, Field

from bot.config import Config, load_config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from bot.tools.work_tools import (
    CreateAttendanceSheetTool,
    GetAttendanceSheetTool,
    SendFileTool,
    ListAttendanceSheetsTool
)
from langchain_core.tools import BaseTool

class WorkAgentState(BaseModel):
    """エージェントの状態"""

    user_name: str = Field(default="作業を依頼したユーザ名")
    user_query: str = Field(default="依頼された作業内容")

class WorkAgent:
    """ワークチャットボットのエージェント"""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.tools = []

    def add_tool(self, tool: BaseTool):
        self.tools.append(tool)

    def invoke(self, state: WorkAgentState) -> Iterator[str]:
        agent = create_react_agent(self.llm, self.tools)

        """エージェントを呼び出す"""
        stream = agent.stream({
            "messages": [
                (
                    "system",
                    "あなたは会社内部で働くフレンドリーな友達です。\n"
                    "会社外部で働くユーザのために依頼された作業をルールに従って行なってください。\n"
                    "ルール:\n"
                    "- 1. ユーザの依頼内容に応じて、ツールを使用して作業を行なってください。\n"
                    "- 2. 作業前に応答を返し、その後作業に入ってください。\n"
                    "- 3. 作業進捗を事細かくユーザに伝えてください。\n"
                    "- 4. 作業完了後は**必ず**結果をユーザに伝えて締めくくってください。\n"
                    "- 5. ツール実行結果がエラーの場合は、正常に実行できなかった旨のメッセージを返却してください。\n"
                    "- 6. ユーザが勤怠表を作成依頼した場合、次の手順を踏んでください。\n"
                    "   - a. ツールを使って勤怠表を作成する。\n"
                    "   - b. aの返却値を使って、ツールを使って勤怠表をユーザに送信する。\n"
                ),
                (
                    "user",
                    f"ユーザ名: {state.user_name}\n"
                    f"ユーザの依頼内容:\n{state.user_query}"
                )
            ]
        })
        for chunk in stream:
            if not chunk.get("agent"):
                continue
            messages = chunk.get("agent").get("messages")
            if not messages or len(messages) == 0:
                continue
            ai_message = messages[0]
            if ai_message.content and isinstance(ai_message.content, str):
                yield ai_message.content

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
    ) -> Iterator[str]:
        """チャットボットにメッセージを送信し、ストリーミング形式で返答を返します。"""
        state = WorkAgentState(user_name=user_name, user_query=message)
        return self.agent.invoke(state)

if __name__ == "__main__":
    config = load_config()
    llm = ChatGoogleGenerativeAI(
        model=config.google_gemini_model_name,
    )
    chatbot = WorkChatbot(config, llm)
    chatbot.add_tool(CreateAttendanceSheetTool())
    chatbot.add_tool(GetAttendanceSheetTool())
    chatbot.add_tool(SendFileTool())
    chatbot.add_tool(ListAttendanceSheetsTool())
    for response in chatbot.chat("僕の勤怠表送って", "やまだ"):
        print(response)