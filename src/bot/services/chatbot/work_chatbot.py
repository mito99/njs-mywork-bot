import logging
from typing import Iterator

from pydantic import BaseModel, Field

from bot.config import Config, load_config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from langchain.memory import ConversationBufferMemory
from bot.tools.work_tools import (
    CreateAttendanceSheetTool,
    ListFilesTool,
    SendFileTool,
)
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, trim_messages

logger = logging.getLogger(__name__)
class WorkAgentState(BaseModel):
    """エージェントの状態"""

    user_name: str = Field(default="作業を依頼したユーザ名")
    user_query: str = Field(default="依頼された作業内容")

class WorkAgent:
    """ワークチャットボットのエージェント"""

    def __init__(self, llm: BaseChatModel, memory: MemorySaver):
        self.llm = llm
        self.tools = []
        self.memory = memory
        # 初期化時にSystemMessageを設定
        self.system_message = SystemMessage(
            content="あなたは会社内部で働くフレンドリーな友達です。\n"
            "会社外部で働くユーザのために依頼された作業をルールに従って行なってください。\n"
            "ルール:\n"
            "- 1. ユーザの依頼内容に応じて、ツールを使用して作業を行なってください。\n"
            "- 2. ユーザからの要求が理解できない場合、ユーザに質問をしてください。\n"
            "- 3. 作業前に応答を返し、その後作業に入ってください。\n"
            "- 4. 作業進捗を事細かくユーザに伝えてください。\n"
            "- 5. 作業完了後は**必ず**結果をユーザに伝えて締めくくってください。\n"
            "- 6. ツール実行結果がエラーの場合は、正常に実行できなかった旨のメッセージを返却してください。\n"
            "- 7. ユーザがファイルを要求した場合ファイルパスを含めツールを呼び出してください。\n"
        )
        self.trimmer = trim_messages(
            max_tokens=10,
            strategy="last",
            token_counter=len,
            include_system=True,
            allow_partial=False,
            start_on="human",
        )

    def add_tool(self, tool: BaseTool):
        self.tools.append(tool)

    def invoke(self, state: WorkAgentState, config: dict) -> Iterator[str]:
        # ユモリから既存のメッセージを取得
        checkpoint = self.memory.get_tuple(config)
        messages = []
        
        if checkpoint:
            channel_values = checkpoint.checkpoint.get('channel_values')
            if channel_values:
                messages = channel_values.get('messages')
        else:
            # 初回の場合はシステムメッセージを追加
            messages = [self.system_message]
        
        # ユーザメッセージを追加
        user_message = HumanMessage(
            content=f"ユーザ名: {state.user_name}\n"
            f"ユーザの依頼内容:\n{state.user_query}"
        )
        messages.append(user_message)

        agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory,
        )

        trimmed_messages = self.trimmer.invoke(messages)
        stream = agent.stream(
            {"messages": trimmed_messages}, 
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

    def __init__(self, config: Config, llm: BaseChatModel, memory: ConversationBufferMemory):
        self.config = config
        self.agent = WorkAgent(llm, memory)

    def add_tool(self, tool: BaseTool):
        self.agent.add_tool(tool)

    def stream_chat(
        self,
        message: str,
        user_name: str,
        thread_ts: str,
    ) -> Iterator[str]:
        """チャットボットにメッセージを送信し、ストリーミング形式で返答を返します。"""
        state = WorkAgentState(user_name=user_name, user_query=message)
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