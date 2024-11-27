import asyncio
from telegram import Update
from telegram.ext import (Application,
                          CommandHandler,
                          MessageHandler,
                          filters,
                          TypeHandler,
                          )

from .handlers import handle_message, send_message_from_pubsub, error_handler, help_command, start_command, whitelist_user
from . import BaseInterface, TelegramSettings, logger


class TelegramInterface(BaseInterface):
    def __init__(self,
                 token,
                 config: TelegramSettings,
                 pubsub: 'PubSub',
                 publish_to: str,
                 subscribe_to: str,
                 creator_username: str
                 ):
        super().__init__(pubsub)

        # config variables
        self.CREATOR_ID = config.creator_id
        self.CREATOR_USERNAME = creator_username
        self.publish_to = publish_to
        self.subscribe_to = subscribe_to
        logger.info(f"[TelegramInterface/__init__] Building an Application")
        self.app: Application = Application.builder().token(token).build()

        # for the access in handlers
        self.app.context_types.context.bot_data = {
            "creator_id": self.CREATOR_ID,
            'creator_username': self.CREATOR_USERNAME,
            'pubsub': self.pubsub,
            'publish_to': self.publish_to
        }

        self.job_queue = self.app.job_queue
        logger.info(f'[TelegramInterface/__init__] Subscribed to {self.subscribe_to}')
        self.pubsub.subscribe(self.subscribe_to, send_message_from_pubsub)
        # self.job_queue.run_repeating()

    def initialize(self):
        logger.info(f"[TelegramInterface/initialize] Initialization of telegram handlers.")
        filter_users = TypeHandler(Update, whitelist_user)
        self.app.add_handler(filter_users, -1)

        self.app.add_handlers([
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            MessageHandler(filters.TEXT, handle_message),
        ])
        self.app.add_error_handler(error_handler)

    def stop(self):
        logger.warning(f"[telegram_bot/stop] Not implemented on windows")

    def manage_event_loop(self):
        """
        Creates a new event loop and runs the asynchronous tasks.
        This method should be called when using asyncio-based models.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info('[TelegramInterface/manage_even_loop] Created new event loop')
        return loop

    def run(self):
        try:
            loop = self.manage_event_loop()
            self.initialize()
            logger.info(f"[Telegram/run] Starting an Application.")
            loop.run_until_complete(self.app.run_polling(drop_pending_updates=True))
        except Exception as e:
            logger.exception("An error occurred in the bot thread: %s", e)

