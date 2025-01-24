import asyncio
import logging

from njs_mywork_tools.mail import MailWatcher
from njs_mywork_tools.mail.models.message import MailMessage
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
        
        while True:
            try:
                watcher = await MailWatcher.start(self.config.surrealdb)
                async for mail in watcher.watch_mails():
                    try:
                        action = mail["action"]
                        if action != "CREATE":
                            continue
                        
                        mail_msg: MailMessage = mail["mail_msg"]
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
                        logger.error(f"メール処理エラー: {e}")
                        
            except ConnectionError as e:
                logger.error(f"接続エラーが発生しました: {e}. 再接続を試みます...")
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"予期せぬエラー: {e}. アプリを再起動します")
                await asyncio.sleep(30)

    def _create_app(self, config: Config) -> AsyncApp:
        app = AsyncApp(token=config.slack_bot_mail.bot_token)
        return app
