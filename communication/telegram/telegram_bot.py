import asyncio
import signal

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
from .handlers import handle_message, send_message, error, help_command, start_command, whitelist_user
from config import TelegramSettings, logger


class TelegramInterface(BaseInterface):
    def initialize(self):
        filter_users = TypeHandler(Update, whitelist_user)
        self.app.add_handler(filter_users, -1)

        self.app.add_handlers([
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CommandHandler("stop", self.stop_command),  # Handle /stop command
            MessageHandler(filters.TEXT, handle_message),
            # MessageHandler(filters.VOICE, handle_voice),
        ])

    async def stop_command(self, update: Update, context):
        """Handle /stop command to stop the AI assistant."""
        # Check if the user is authorized
        if update.effective_user.id == self.CREATOR_ID:
            await update.message.reply_text("Stopping the AI Assistant...")
            await self.stop_queue.put('stop')
        else:
            await update.message.reply_text("You are not authorized to stop the bot.")

    def __init__(self,
                 token,
                 config: TelegramSettings,
                 stop_queue,
                 pubsub: 'PubSub',
                 publish_to: str,
                 subscribe_to: str,
                 ):
        # essential variables
        super().__init__(pubsub)

        self.CREATOR_ID = config.creator_id
        self.CREATOR_USERNAME = config.creator_username
        self.stop_queue = stop_queue
        self.publish_to = publish_to
        self.subscribe_to = subscribe_to

        # defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=pytz.timezone(self.country))
        # self.app: Application = Application.builder().token(token).defaults(defaults).build()
        self.app: Application = Application.builder().token(token).build()

        self.app.context_types.context.bot_data = {
            "creator_id": self.CREATOR_ID,
            'pubsub': self.pubsub,
            'publish_to': self.publish_to
        }

        self.job_queue = self.app.job_queue
        self.pubsub.subscribe(self.subscribe_to, send_message)
        # self.job_queue.run_repeating()

    def stop(self):
        logger.warning(f"[telegram_bot/stop] Not implemented on windows")

    def manage_event_loop(self):
        """
        Creates a new event loop and runs the asynchronous tasks.
        This method should be called when using asyncio-based models.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

    def run(self):
        try:
            loop = self.manage_event_loop()
            self.initialize()
            loop.run_until_complete(self.app.run_polling(drop_pending_updates=True))
        except Exception as e:
            logger.exception("An error occurred in the bot thread: %s", e)

