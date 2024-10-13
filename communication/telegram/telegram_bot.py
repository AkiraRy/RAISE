import asyncio

import pytz
from .. import BaseInterface
from telegram import Update, InputFile, Voice
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (Application,
                          CommandHandler,
                          MessageHandler,
                          filters,
                          ContextTypes,
                          Defaults,
                          ApplicationHandlerStop,
                          TypeHandler,
                          )
import config.settings as settings
from .handlers import handle_message, error, help_command, start_command, whitelist_user
import logging
logger = logging.getLogger("bot")


class TelegramInterface(BaseInterface):
    def initialize(self):
        filter_users = TypeHandler(Update, whitelist_user)
        self.app.add_handler(filter_users, -1)

        self.app.add_handlers([
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            MessageHandler(filters.TEXT, handle_message),
            # MessageHandler(filters.VOICE, handle_voice),
        ])

    async def tts(self, message: str):
        pass

    async def stt(self, intput: bytes):
        pass

    async def llm_interfere(self, message: str):
        pass

    def __init__(self, token, config):
        # essential variables
        self.CREATOR_ID = config.get("CREATOR_ID", None)
        # self.CREATOR_USERNAME = config.get('CREATOR_USERNAME", None)
        self.country = config.get("Country", "UTC")

        defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=pytz.timezone(self.country))
        self.app: Application = Application.builder().token(token).defaults(defaults).build()
        self.app.context_types.context.bot_data = {
            "creator_id": self.CREATOR_ID,
            "country": self.country,
        }

        # self.job_queue = self.app.job_queue
        # self.job_queue.run_repeating()

    # def just_start_please(self):
    #     self.initialize()
    #     self.app.run_polling()

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.initialize()
            loop.run_until_complete(self.app.run_polling())
        except Exception as e:
            logger.exception("An error occurred in the bot thread: %s", e)

