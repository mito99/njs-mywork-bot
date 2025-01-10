import asyncio
import logging
from time import sleep

from njs_mywork_tools.mail import MailWatcher

from bot.config import Config, load_config
from bot.slack_app import create_app, start_socket_mode
from bot.utils.logging import setup_logging


async def subscribe_mail(config: Config):
    watcher = await MailWatcher.start(config.surrealdb)
    async for mail in watcher.watch_mails():
        print(mail)

async def main():
    config = load_config()
    
    setup_logging(config.application.log_level)
    app = create_app(config)

    # メール監視のタスクとして実行
    task1 = asyncio.create_task(subscribe_mail(config))
    # Slackのソケットモードを起動
    task2 = asyncio.create_task(start_socket_mode(app, config))

    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())
