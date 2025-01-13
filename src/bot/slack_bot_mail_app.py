import logging

from njs_mywork_tools.mail import MailWatcher
from slack_bolt.async_app import AsyncApp

from bot.config import Config
from bot.services.chatbot.mail_chatbot import SummarizeMailChatbot

logger = logging.getLogger(__name__)

class SlackBotMailApp:
    def __init__(self, config: Config):
        self.config = config
        self.app = self._create_app(config)
        self.channel_id = config.slack_bot_mail.channel_id

    async def subscribe_mail(self):
        summarize_mail_chatbot = SummarizeMailChatbot(self.config)
        watcher = await MailWatcher.start(self.config.surrealdb)
        async for mail in watcher.watch_mails():
            try:
                action = mail["action"]
                if action != "CREATE":
                    continue
                
                mail_msg = mail["mail_msg"]
                if mail_msg is None:
                    logger.error("メールが取得できない")
                    continue
                
                if self.config.is_ignore_mail(mail_msg.sender):
                    logger.info(f"メールを無視します: {mail_msg.sender}")
                    continue
                
                summary = summarize_mail_chatbot.invoke(mail_msg)
                result = await self.app.client.chat_postMessage(
                    channel=self.channel_id, 
                    text=(
                        "----------------------------------------------\n"
                        f"{summary}\n"
                        "----------------------------------------------\n"
                    )
                )
            except Exception as e:
                logger.error(f"メール送信中にエラーが発生: {e}")

    def _create_app(self, config: Config) -> AsyncApp:
        app = AsyncApp(token=config.slack_bot_mail.bot_token)
        return app