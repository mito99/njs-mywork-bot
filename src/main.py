import asyncio
import logging
from time import sleep

from njs_mywork_tools.mail import MailWatcher

from bot.config import Config, load_config
from bot.slack_bot_mail_app import SlackBotMailApp
from bot.slack_bot_task_app import SlackBotTaskApp
from bot.utils.logging import setup_logging


async def main():
    config = load_config()
    
    setup_logging(config.application.log_level)

    # メール監視のタスクとして実行
    slack_bot_mail_app = SlackBotMailApp(config)    
    task_bot_mail = asyncio.create_task(slack_bot_mail_app.subscribe_mail())
    
    # Slackのソケットモードを起動
    slack_task_bot_app = SlackBotTaskApp(config)
    task_bot_task = asyncio.create_task(slack_task_bot_app.start_socket_mode())

    await asyncio.gather(task_bot_mail, task_bot_task)

if __name__ == "__main__":
    asyncio.run(main())
