import os
import threading
from utils import Message, TextMessage, TelegramMessage
from telegram import Update, constants
from telegram.ext import CallbackContext, ContextTypes, ApplicationHandlerStop
import logging
logger = logging.getLogger("bot")


async def whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

def func():
    print(3)


async def send_message(message: TelegramMessage):
    content = message.response_message['content']
    await message.update.message.reply_text(content)


async def handle_message(update: Update, context: CallbackContext):
    # add here preprocessing of the image so on so on

    pubsub = context.bot_data['pubsub']
    topic = context.bot_data['publish_to']

    user_input = update.message.text
    msg_cls = TelegramMessage(update.message.id, text_message=TextMessage(user_input), update=update, context=context)

    pubsub.publish(topic, msg_cls)
    # This is where you can connect to the assistant core
    response = f"You said: {user_input}"

    # timer = threading.Timer(3, func)
    # timer.start()
    # await update.message.reply_text(response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
