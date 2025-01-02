from typing import Iterator

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from bot.config import Config


class SimpleChatbot:
    """チャットボットのサービス"""

    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatGoogleGenerativeAI(
            model=config.google_gemini_model_name,
        )

    def stream_chat(self, message: str, user_name: str) -> Iterator[str]:
        """チャットボットにメッセージを送信し、ストリーミング形式で返答を返します。"""
        prompt = ChatPromptTemplate.from_template(
            "あなたは気さくなアシスタントロボです。"
            "ユーザからのメッセージを受け取りユーザに対して返答を行います。\n"
            "ユーザ名: {user_name}\n"
            "ユーザからのメッセージ:\n"
            "{message}"
        )
        chain = prompt | self.llm | StrOutputParser()
        return chain.stream({"message": message, "user_name": user_name})
