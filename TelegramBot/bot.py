import os
import sys
from collections import deque
import threading
import time
from datetime import datetime

from Kurisu.kurisu import Kurisu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytz
import emoji
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (Application,
                          CommandHandler,
                          MessageHandler,
                          filters,
                          ContextTypes,
                          Defaults,
                          ApplicationHandlerStop,
                          TypeHandler)

from stickersu import getSticker, add_stickerInfo, checkStickers
from textGen import run
import requests
from dotenv import load_dotenv
from collections import deque
load_dotenv()

BOT_USERNAME = os.getenv("BOT_NAME")
TOKEN = os.getenv("TG_TOKEN")
COUNTRY : str= os.getenv('PLACE')
CREATOR_ID  = int(os.getenv('CREATOR_ID'))
CREATOR_USERNAME = os.getenv('CREATOR_USERNAME')

kurisu = Kurisu([{}])
chat_queue: list= []


async def whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE ):
    if update.effective_chat.id != CREATOR_ID or update.message.chat.type != 'private':
        await update.effective_message.reply_text('Be patient. This AI bot is not available for anyone')
        raise ApplicationHandlerStop

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

async def handle_response() :
    prompt = await kurisu.fulfilingPrompt()

    try:
        user_name = chat_queue[0]['from']
        text = chat_queue[0]['message']
        date = chat_queue[0]['datetime']
        prompt = prompt .replace('<|DATETIME|>', date[:-6])
        ctx = await kurisu.memory_context(text)
        if ctx is not None:
            context = '\n'.join([f"{elems['from']}: {elems['message']}" for elems in ctx])
            prompt = prompt.replace('<|CONTEXT|>', context)
        prompt = prompt.replace('<input>', text)
        response = run(prompt=prompt)

        print(prompt)
        memory = [
            {
                'name': user_name,
                'message': text,
                'datetime': date
            },
            {
                'name': 'Kurisu',
                'message': response,
                'datetime': pytz.timezone(COUNTRY).localize(datetime.now()).isoformat(timespec="seconds")
            }
        ]
        # await kurisu.add_memories(memory)
        prompt+=response
        print(prompt)

        chat_queue.pop(0)
        return response

    except requests.exceptions.Timeout:
        print('Request timeout')
        return None
    except requests.exceptions.ConnectionError:
        return 'Unable to reach Kurisu, make sure she is not sleeping'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.message.from_user
    fromU = update.message.from_user.id


    message: str = update.message.text
    datetimeU = update.message.date.isoformat() # - format datetime to store in vdb

    message = emoji.replace_emoji(message, replace='').strip()
    if not message: return

    if len(chat_queue) > 0:
        await update.message.reply_text("Wait a little bit, Kurisu is typing")
        return
    else :
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        chat_queue.append({
            'from': CREATOR_USERNAME if CREATOR_ID == sender.id else f'{sender.full_name}',
            'message': message,
            'datetime': datetimeU
        })

        response: str = await handle_response()

        if response is None:
            return
        await update.message.reply_text(response)

# Errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'error {context.error} from {update}')

#for future make it in threads
def process_chat_queue():
    while True:
        if chat_queue:
            # Process the chat_queue here
            item = chat_queue.pop(0)


            print("Processing item:", item)


        time.sleep(1)

if __name__ == '__main__':
    print('starting bot')
    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=pytz.timezone(COUNTRY))
    app = (
        Application.builder()
        .token(TOKEN)
        .defaults(defaults)
        .build()
    )

    filter_users = TypeHandler(Update, whitelist_user)
    app.add_handler(filter_users, -1)

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('sticker', send_sticker))

    # Messages
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Error
    app.add_error_handler(error)
    user_states = {}
    app.context_types.context.user_states = user_states

    # chat_queue_thread = threading.Thread(target=process_chat_queue)
    # chat_queue_thread.start()
    app.run_polling()