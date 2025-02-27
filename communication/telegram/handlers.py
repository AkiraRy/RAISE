import asyncio
import datetime

from utils import Message_server
from telegram import Update, constants
from telegram.ext import CallbackContext, ContextTypes, ApplicationHandlerStop
from telegram.constants import ChatAction, ParseMode
import re
from . import logger
import io


async def whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.bot_data["creator_id"]:
        return False
    if update.effective_chat.id != int(context.bot_data["creator_id"]) or update.message.chat.type != 'private':
        await update.effective_message.reply_text('Be patient. This AI bot is not available for anyone')
        logger.warning(f"[Telegram/whitelist] User({update.effective_chat.id}:id)")
        raise ApplicationHandlerStop


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(':smile:')
    logger.info(f'[Telegram/start] USER({update.message.chat.id}) in {update.message.chat.type}: "{update.message.text}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"[Telegram/help] User({update.effective_chat.id}:id). IMPLEMENT HELP!!!")
    await update.message.reply_text('help')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # it is still kinda same update, but i have no idea why they changed it to object
    logger.error(f'[error] USER({update.message.chat.id}) in {update.message.chat.type}: {context.error} from {update}')


async def handle_message(update: Update, context: CallbackContext):
    creator_name = context.bot_data['creator_username']
    brain_helper = context.bot_data['brain']

    sender = update.message.from_user
    message_from_user = update.message.text
    datetime_msg = datetime.datetime.now().astimezone()
    # add library or regex to filter out emojis

    logger.debug(f"[Telegram/handle_message] We got message from the user: {sender.id}, content: {message_from_user}")
    message_srv = Message_server(
        id=update.message.id,
        from_user=creator_name,
        datetime=datetime_msg,
        text_content=message_from_user
    )

    logger.info(f"[Telegram/handle_message] Sending message to brain handler")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    response = await brain_helper.generate_response(message_srv)
    if response is None:
        await update.message.reply_text("No generated response")
        return

    await update.message.reply_text(response)


async def handle_files(*args, **kwargs):
    raise NotImplemented


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check for whisper connectivity.
    plugin_manager = context.bot_data['plugin_manager']

    voice_file = await context.bot.get_file(update.message.voice.file_id)

    buffer = io.BytesIO()
    await voice_file.download_to_memory(buffer)
    buffer.seek(0)


    try:
        # check if connected first, do that tomorrow

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
        response = await plugin_manager.transcribe(buffer)
    except requests.exceptions.ConnectionError:
        print('whisper cannot transcribe')
        return

    print(f'the response {response}')

    # Clearing the response
    speech = re.sub('Kurisu', '', response.strip(), flags=re.IGNORECASE)
    reply_text = f'<i>Heard: \"{speech}\"</i>'

    # Get the ID of the message to reply to
    reply_to_message_id = update.message.message_id

    # Send the reply message as a reply to the specific message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_text,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=reply_to_message_id
    )
