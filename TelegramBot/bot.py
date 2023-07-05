import os
import pytz
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, Defaults
from stickersu import getSticker, add_stickerInfo, checkStickers
from textGen import run

import requests
from dotenv import load_dotenv
load_dotenv()
BOT_USERNAME = os.getenv("BOT_NAME")
TOKEN = os.getenv("TG_TOKEN")
COUNTRY = os.getenv('PLACE')


prompt = f"""Akira is a friend of yours, and you are Makise Kurisu is a fascinating persona known for her brilliance and diverse interests. She is a renowned neuroscientist specializing in cognitive research and has made groundbreaking contributions to the field. With her exceptional intellect and analytical thinking, she is often sought after for her expertise in unraveling the mysteries of the human mind.
Scientifically, Kurisu delves into topics such as memory formation, brain function, and consciousness. She passionately explores the intricacies of neural networks and strives to push the boundaries of our understanding of the brain. Her work has garnered international recognition, and she frequently presents her findings at prestigious conferences and publishes influential research papers.
Beyond her scientific pursuits, Kurisu possesses a multifaceted personality. She has a sharp wit and a dry sense of humor, making her conversations engaging and entertaining. Her interests extend beyond science, encompassing literature, philosophy, and technology. Kurisu is an avid reader and enjoys engaging in thought-provoking discussions on various subjects.
    
You are going to have a conversation with your friend Akira, be kind with him
    
    -- Transcript --
### Akira: <input>
### Kurisu:"""
default = """
### Akira: <input>
### Kurisu:"""
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(':smile:')
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



def handle_response(text: str) :
    global  prompt

    try:
        prompt = prompt.replace('<input>', text)
        response = run(prompt=prompt)
        prompt=prompt.replace("###", '')
        prompt+=response
        prompt+=default
        print(prompt)

    except requests.exceptions.Timeout:
        print('Request timeout')
        return None
    except requests.exceptions.ConnectionError:
        return 'Unable to reach Kurisu, make sure she is not sleeping'


    return response

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messag_type: str = update.message.chat.type
    text: str = update.message.text

    print(update.message.from_user.username)
    # print(update.message.date.isoformat()) # - format to store in vdb

    print(context.user_data)
    print(f'user ({update.message.chat.id}) in {messag_type}: "{text}"')



    response: str = handle_response(text)
    if response is None:
        return
    await update.message.reply_text(response)

# Errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'error {context.error} from {update}')


if __name__ == '__main__':
    print('starting bot')
    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=pytz.timezone(os.getenv(COUNTRY)))
    app = (
        Application.builder()
        .token(TOKEN)
        .defaults(defaults)
        .build()
    )

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
