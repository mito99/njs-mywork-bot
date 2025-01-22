import logging
from datetime import datetime

from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from njs_mywork_tools.mail.models.message import MailMessage

from bot.config import Config

logger = logging.getLogger(__name__)

weekday_ja = {
    0: '月',
    1: '火', 
    2: '水',
    3: '木',
    4: '金',
    5: '土',
    6: '日'
}

def format_datetime_ja(dt: datetime):
    date = dt.strftime("%Y-%m-%d")
    weekday = weekday_ja[dt.weekday()]
    time = dt.strftime("%H:%M")
    return f"{date} ({weekday}) {time}"

class SummarizeMailChatbot:
    """メールチャットボット"""

    def __init__(self, config: Config):
        self.llm = self._init_bedrock_chat(config)
        self.tools = []
        
    def _init_bedrock_chat(self, config: Config):
        return ChatBedrock(
            model_id=config.aws.model_id,
            region_name=config.aws.default_region,
            aws_access_key_id=config.aws.access_key_id,
            aws_secret_access_key=config.aws.secret_access_key,
            model_kwargs={
                "temperature": 0,
                "top_p": 1,
            }
        )
        
    def invoke(self, mail: MailMessage): 
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
                "メールの内容をSlack通知用に最適化して圧縮するプロンプトです。\n"
                "入力：\n"
                "- メールの本文\n"
                "- メールのメタデータ（件名、送信者、受信日時）\n"
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
                "📧 [件名]\n"
                "受信: [受信日時]\n"
                "ID: [メールID]\n\n"
                "TO: [宛先]\n"
                "CC: [CC]\n"
                "FROM: [送信者]\n\n"
                "[圧縮された本文]\n"
                "添付: [ファイル名（あれば）]\n\n"
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
                "宛先: {to_addresses}\n"
                "CC: {cc_addresses}\n"
                "送信者: {sender}\n"
                "受信日時: {received_at}\n"
                "本文: {body}\n"
                "添付ファイル: {attachments}"
            )
        ])
        
        
        attachments = ",".join([
            f"{file_name}"
            for file_name in mail.attachments
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({
            "mail_id": mail.id,
            "subject": mail.subject,
            "to_addresses": ", ".join(mail.to_addresses),
            "cc_addresses": ", ".join(mail.cc_addresses),
            "sender": mail.sender,
            "received_at": format_datetime_ja(mail.received_at),
            "body": mail.body,
            "attachments": attachments
        })