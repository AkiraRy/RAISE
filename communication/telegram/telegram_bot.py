import asyncio
from telegram import Update
from telegram.ext import (Application,
                          CommandHandler,
                          MessageHandler,
                          filters,
                          TypeHandler,
                          )

from .handlers import handle_message, error_handler, help_command, start_command, whitelist_user, handle_voice
from . import BaseInterface, TelegramSettings, logger
from core import BrainHelper, PMHelper


class TelegramInterface(BaseInterface):
    def __init__(self,
                 token,
                 config: TelegramSettings,
                 creator_username: str,
                 brain: BrainHelper,
                 plugin_manager: PMHelper):

        # config variables
        self.config = config
        self.CREATOR_ID = config.creator_id
        self.CREATOR_USERNAME = creator_username
        self.brain = brain
        self.plugin_manager = plugin_manager
        logger.info(f"[TelegramInterface/__init__] Building an Application")
        self.app: Application = Application.builder().token(token).build()

        # for the access in handlers
        self.app.context_types.context.bot_data = {
            "creator_id": self.CREATOR_ID,
            'creator_username': self.CREATOR_USERNAME,
            "brain": self.brain,
            "plugin_manager": self.plugin_manager,
            "answer_voice_messages": self.config.answer_voice_messages,
            "generate_voice_messages": self.config.generate_voice,
        }

        self.job_queue = self.app.job_queue
        # self.job_queue.run_repeating()

    def initialize(self):
        logger.info(f"[TelegramInterface/initialize] Initialization of telegram handlers.")
        filter_users = TypeHandler(Update, whitelist_user)
        self.app.add_handler(filter_users, -1)

        self.app.add_handlers([
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            MessageHandler(filters.TEXT, handle_message),
            MessageHandler(filters.VOICE, handle_voice),
        ])
        self.app.add_error_handler(error_handler)

    def stop(self):
        logger.warning(f"[telegram_bot/stop] Not implemented on windows")
        raise NotImplemented()

    def manage_event_loop(self):
        """
        deprecated, still in use because everything fails unless used in this manor :happydays:
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
            logger.info(f"[Telegram/run] Starting an Application.")
            loop.run_until_complete(self.app.run_polling(drop_pending_updates=True))
        except Exception as e:
            logger.exception("An error occurred in the bot thread: %s", e)

