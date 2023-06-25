import os
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from stickersu import getSticker, add_stickerInfo, checkStickers
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_USERNAME = os.getenv("BOT_NAME")
TOKEN = os.getenv("TG_TOKEN")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('hello!')
    print(f'user ({update.message.chat.id}) in {update.message.chat.type}: "{update.message.text}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('help')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('custom')


async def send_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.split(" ")[1]

    name = "kurisureac"
    sticker_set = await context.bot.get_sticker_set(name=name)  # create a method to add more available stickers
    stickers_info = {}
    for sticker in sticker_set.stickers:
        emoji = sticker.emoji
        file_id = sticker.file_id
        stickers_info[emoji] = stickers_info.get(emoji, []) + [file_id]

    if not await checkStickers(name):
        await add_stickerInfo(name, stickers_info)

    sticker = await getSticker(name, message)
    if sticker is not None:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=await getSticker(name, message))
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await update.message.reply_text(f"There is no such emoji {message}")


# Responses
# user (728212232)
# nivvada
# await bot.send_message(chat_id=chat_id, text="I'm sorry Dave I'm afraid I can't do that.")
def handle_response(text: str) :
    text: str = text.lower()
    BASE_URL = 'http://8f8b-34-82-137-55.ngrok-free.app'
    url = f"{BASE_URL}/asr"
    task = 'llm'
    files = {'text': text}
    params = {'task': task}
    try:
        r = requests.post(url, params=params, files=files)
    except requests.exceptions.Timeout:
        print('Request timeout')
        return None

    except requests.exceptions.ConnectionError:
        print(
            'Unable to reach Whisper, ensure that it is running, or the WHISPER_BASE_URL variable is set correctly')
        return None

    return r.text




async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messag_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'user ({update.message.chat.id}) in {messag_type}: "{text}"')

    if messag_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return

    response: str = handle_response(text)
    if response is None:
        return
    await update.message.reply_text(response)


# Erors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'error {context.error} from {update}')


if __name__ == '__main__':
    print('starting bot')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('sticker', send_sticker))

    # Messages
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Error

    app.add_error_handler(error)
    print('polling')
    app.run_polling(poll_interval=3)
