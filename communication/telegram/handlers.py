import os

from telegram import Update, constants
from telegram.ext import CallbackContext, ContextTypes, ApplicationHandlerStop
import logging
logger = logging.getLogger("bot")


async def whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("wf")
    if not context.bot_data["creator_id"]:
        return False
    if update.effective_chat.id != int(context.bot_data["creator_id"]) or update.message.chat.type != 'private':
        await update.effective_message.reply_text('Be patient. This AI bot is not available for anyone')
        logger.warning(f"[whitelist] User({update.effective_chat.id}:id)")
        raise ApplicationHandlerStop


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(':smile:')
    logger.info(f'[/start] USER({update.message.chat.id}) in {update.message.chat.type}: "{update.message.text}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('help')


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'[error] USER({update.message.chat.id}) in {update.message.chat.type}: {context.error} from {update}')


async def handle_message(update: Update, context: CallbackContext):
    """Process a message from the user."""
    print(context.bot_data)
    user_input = update.message.text
    # This is where you can connect to the assistant core
    response = f"You said: {user_input}"
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
