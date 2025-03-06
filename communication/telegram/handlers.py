import datetime

from utils import Message_server
from telegram import Update, constants, File
from telegram.ext import CallbackContext, ContextTypes, ApplicationHandlerStop
from telegram.constants import ChatAction, ParseMode
from utils.helper_functions import translate_text
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
    plugin_manager = context.bot_data['plugin_manager']  # make a helper function for getting all of that mess
    generate_voice_messages = context.bot_data['generate_voice_messages']

    # metadata
    sender = update.message.from_user
    message_from_user = update.message.text
    datetime_msg = datetime.datetime.now().astimezone()
    chat_id = update.effective_chat.id
    mssg_id = update.message.id

    # add library or regex to filter out emojis

    logger.debug(f"[Telegram/handle_message] We got message from the user: {sender.id}, content: {message_from_user}")

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    response = await get_response(brain_helper, mssg_id, creator_name, datetime_msg, message_from_user)

    if response is None:
        await update.message.reply_text("No generated response")
        return

    await update.message.reply_text(response)

    if not generate_voice_messages:
        # possible debug msg?
        return

    await _send_voice(context, response, plugin_manager, chat_id)


async def _send_voice(context: ContextTypes.DEFAULT_TYPE, response, plugin_manager, chat_id):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
    voice_bytes = await _generated_voice(plugin_manager, response)  # what f genius
    if not voice_bytes:
        logger.warning(f"[Telegram/_send_voice], no voice data was generated")
        return
    await context.bot.send_voice(chat_id=chat_id, voice=voice_bytes)


async def get_response(brain_helper, mssg_id, creator_name, datetime_msg, message_from_user):
    message_srv = Message_server(
        id=mssg_id,
        from_user=creator_name,
        datetime=datetime_msg,
        text_content=message_from_user
    )

    logger.info(f"[Telegram/handle_message] Sending message to brain handler")
    return await brain_helper.generate_response(message_srv)


async def handle_files(*args, **kwargs):
    raise NotImplemented


async def _transcribe(plugin_manager, voice_file: File):
    # generates txt from voice
    buffer = io.BytesIO()
    await voice_file.download_to_memory(buffer)
    buffer.seek(0)
    return await plugin_manager.transcribe(buffer)


async def _generated_voice(plugin_manager, text: str):
    # preprocess text
    text = text.strip()
    # add possible regex as well?
    return await plugin_manager.tts(text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plugin_manager = context.bot_data['plugin_manager']  # make a helper function for getting all of that mess
    answer_voice_message = context.bot_data['answer_voice_messages']
    generate_voice_messages = context.bot_data['generate_voice_messages']
    brain_helper = context.bot_data['brain']
    creator_name = context.bot_data['creator_username']

    if not await plugin_manager.is_plugin_loaded("whisper"):
        logger.warning(f"[Telegram/handle_voice] Whisper is not loaded. Cant transcribe.")
        return False

    # metadata
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    chat_id = update.effective_chat.id
    mssg_id = update.message.id
    datetime_msg = datetime.datetime.now().astimezone()

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
    response = await _transcribe(plugin_manager, voice_file)
    # check if response is null first

    # Get the ID of the message to reply to
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'<i>Heard: \"{response}\"</i>',
        parse_mode=ParseMode.HTML,
        reply_to_message_id=mssg_id
    )

    if not answer_voice_message:
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    response = await get_response(brain_helper, mssg_id, creator_name, datetime_msg, response)

    if response is None:
        # log
        await update.message.reply_text("No generated response")
        return

    await update.message.reply_text(response)

    if not generate_voice_messages:
        # possible debug msg?
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
    voice_bytes = await _generated_voice(plugin_manager, response)
    await context.bot.send_voice(chat_id=chat_id, voice=voice_bytes)
