import logging

from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from njs_mywork_tools.mail.models import MailMessageEntity

from bot.config import Config

logger = logging.getLogger(__name__)

class SummarizeMailChatbot:
    """メールチャットボット"""

    def __init__(self, config: Config):
        self.llm = self._init_bedrock_chat(config)
        self.tools = []
        
    def _init_bedrock_chat(self, config: Config):
        return ChatBedrock(
            model_id="amazon.nova-micro-v1:0",
            model_kwargs={
                "temperature": 0,
                "top_p": 1,
            }
        )
        
    def invoke(self, mail: MailMessageEntity): 
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
                "メールの内容をSlack通知用に最適化して圧縮するプロンプトです。\n"
                "入力：\n"
                "- メールのID\n"
                "- メールの本文\n"
                "- メールのメタデータ（件名、送信者、送信日時）\n"
                "- 添付ファイルの情報（存在する場合）\n\n"
                "要件：\n"
                "1. 文字数制限：\n"
                "- 本文は100文字以内に圧縮\n"
                "- 超過する場合は重要度の高い情報を優先\n\n"
                "2. 必ず含めるべき情報：\n"
                "- メールの主題\n"
                "- 重要な日付や締切\n"
                "- 具体的な数値やデータ\n"
                "- アクションアイテム（もしあれば）\n\n"
                "3. 出力フォーマット：\n"
                "メールID: [メールID]\n"
                "📧 [件名]\n"
                "From: [送信者] | 📅 [送信日時]\n"
                "[圧縮された本文]\n"
                "📎 添付: [ファイル名（あれば）]\n\n"
                "4. 圧縮のガイドライン：\n"
                "- 冗長な表現や挨拶文を削除\n"
                "- 箇条書きを活用して情報を整理\n"
                "- 重要なキーワードは保持\n"
                "- 文脈を維持しながら簡潔に表現\n"
                "**重要**:\n"
                "- 出力フォーマット以外の出力は不要。"
            ),
            ("human", 
                "以下のメールを要約してください:\n\n"
                "メールID: {mail_id}\n"
                "件名: {subject}\n"
                "送信者: {sender}\n"
                "受信日時: {received_at}\n"
                "本文: {body}\n"
                "添付ファイル: {attachments}"
            )
        ])
        
        
        attachments = ",".join([
            f"{file.name} ({file.size} bytes)" 
            for file in mail.attachments
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({
            "mail_id": mail.id.split(":")[-1],
            "subject": mail.subject,
            "sender": mail.sender,
            "received_at": mail.received_at,
            "body": mail.body,
            "attachments": attachments
        })