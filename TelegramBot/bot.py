import io
import logging
import os
import subprocess
import sys
from pathlib import Path
import time
from datetime import datetime
import weaviate
from koe.stt import transcribe
from Kurisu.kurisu import Kurisu
import pytz
import soundfile as sf
import emoji
import json
import random
import threading
from translate import Translator
import asyncio
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
from TelegramBot.stickersu import getSticker, add_stickerInfo, checkStickers
from TelegramBot.textGen import run
import requests
import re
from transformers import pipeline
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Plugins')))

load_dotenv()


# Sys Variables
MAIN_PATH = Path(__file__).resolve().parent
TOKEN = os.getenv("TG_TOKEN")
COUNTRY: str = os.getenv('PLACE')
STICKERS_PATH = Path.cwd().parent.absolute() / 'TelegramBot' / os.getenv('STICKERS')
bot = None
feelings_dict: dict = {}
loop = None

# STICKERS_PATH = os.getenv('STICKERS', False)

# To fix asyncio policy on windows
if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# used in gui
def bind(function):
    global bot
    if bot is not None:
        bot.set_function = function


def translate_text(text, target_language, provider="mymemory"):
    if provider == "google":
        provider = "libre"
    translator = Translator(provider=provider, from_lang="en", to_lang=target_language)
    translation = translator.translate(text)
    return translation


def load_stickers():
    """
    format:
    [emotion|..|emotion2],sticker_id_from_telegram, name_of_sticker_pack

    """
    with open(STICKERS_PATH, 'r', encoding='utf-8') as file:
        for line in file:
            list_properties = line.split(',')
            file_id = list_properties[1]
            feelings = list_properties[0].strip('[]').split('|')

            for feeling in feelings:
                feelings_dict.setdefault(feeling, []).append(file_id)


def save_load_stickers():
    if not STICKERS_PATH:
        logging.error("path to sticker is null, couldn't load stickers")
        return
    try:
        load_stickers()
    except IOError:
        logging.error("Couldn't load stickers from file")


def convert_wav_to_ogg(wav_path, output_ogg_path):
    # Use FFmpeg to convert the WAV file to OGG with OPUS encoding
    subprocess.run(['ffmpeg', '-i', wav_path, '-c:a', 'libopus', output_ogg_path])

save_load_stickers()


class MyBot:
    def __init__(self):
        # env values
        self.BOT_USERNAME = os.getenv("BOT_NAME")
        self.NICKNAME = os.getenv('BOT_NICKNAME')
        self.CREATOR_ID = int(os.getenv('CREATOR_ID'))
        self.CREATOR_USERNAME = os.getenv('CREATOR_USERNAME')
        self.AUDIO_DIR = Path(os.getenv('AUDIO_DIR'))
        self.VOICE_FILE = os.getenv('VOICE_FILE')

        # Kurisu(Brain)
        self.classifier = pipeline('sentiment-analysis', model='SamLowe/roberta-base-go_emotions')
        self.kurisu = None
        self.chat_queue: list = []
        self.function = None
        self.activate_kurisu()
        # PARAMETERS TO CONTROL FUNCTIONALITY
        # By default they all will be true and can be changed in gui

        self.VOICE = True  # enables voice from bot
        self.VOICE_CHANGE = True
        self.STICKERS = True  # enables stickers sending from bot
        self.WHISPER = True  # enables transcribing of user voice
        self.REMEMBER = False  # enables memory to db

        # Telegram instance
        self.app = None

        # Voice Instances
        self.voicevox = None
        self.RVC = None
        self.load_voicevox()

    def load_voicevox(self):
        from Plugins.voicevox import  VoicevoxTTSPlugin
        self.voicevox= VoicevoxTTSPlugin()

    # RENAME IT TO LABEL INFO or something similar
    def set_function(self, function):
        self.function = None
        self.function = function

    def activate_kurisu(self):
        if self.kurisu is not None:
            return
        try:
            self.kurisu = Kurisu()
        except:
            logging.critical('Unable to reach Kurisu, make sure she is not sleeping')
            sys.exit(0)

    async def whitelist_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != self.CREATOR_ID or update.message.chat.type != 'private':
            await update.effective_message.reply_text('Be patient. This AI bot is not available for anyone')
            raise ApplicationHandlerStop

    # Not sure if i still need that command
    # maybe host later this telegram bot as separate instance in cloud or rpi
    # so that it cant start a container with llm -gui
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(':smile:')
        print(f'user ({update.message.chat.id}) in {update.message.chat.type}: "{update.message.text}')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('help')

    async def send_sticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
            takes emoji as user input and than sends a sticker from provided sticker pack with chosen emoji

        """

        message = update.message.text.split(" ")[1]

        name = "kurisureac"
        sticker_set = await context.bot.get_sticker_set(name=name)  # Gets all available stickers_id for stk pack
        stickers_info = {}
        for sticker in sticker_set.stickers:
            emj = sticker.emoji
            file_id = sticker.file_id
            stickers_info[emj] = stickers_info.get(emj, []) + [file_id]

        if not await checkStickers(name):
            await add_stickerInfo(name, stickers_info)

        sticker = await getSticker(name, message)
        if sticker is not None:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=await getSticker(name, message))
        else:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            await update.message.reply_text(f"There is no such emoji {message}")

    async def prompt_completion(self) :
        prompt = await self.kurisu.fulfilling_prompt()

        user_name = self.chat_queue[0]['from']
        text = self.chat_queue[0]['message']
        date = self.chat_queue[0]['datetime']


        curr = datetime.fromisoformat(date)
        formatted_datetime = curr.strftime("%d %B %Y, %I:%M%p, %A")  # Timestamp for prompt
        # prompt = prompt.replace('<|DATETIME|>', formatted_datetime)

        # for memory context under the construction
        # ctx = await self.kurisu.memory_context(text)
        # if ctx is not None:
        #     context = '\n'.join([f"{elems['from']}: {elems['message']}" for elems in ctx])
        #     prompt = prompt.replace('<|CONTEXT|>', context)

        prompt[-1]["content"] = text

        # prompt += f"""\n### {user_name}: {text}\n### Kurisu:"""
        # logging.info(prompt) before answer from ai
        return user_name, text, date, self.kurisu.persona , prompt

    async def handle_response(self):
        if len(self.chat_queue) < 1:
            return None

        logging.info('Started generating response to user')

        # Preparing prompt
        user_name, text, date, character_context, prompt = await self.prompt_completion()
        print("\n")
        print(json.dumps(prompt, indent=2))
        print("\n")
        try:
            response, timeR = run(history=prompt, character_context=character_context)
        except requests.exceptions.ConnectionError:
            logging.critical('Unable to reach Kurisu, make sure she is not sleeping')
            return None

        context = self.kurisu.count_tokens()

        # print(f'time: {timeR}, response: {response}, context: {context}')
        logging.info(f'time: {timeR}, response: {response}, context: {context}')
        if self.function is not None:
            print('self function')
            self.function(timeR, context)

        response = response.strip()

        memory = [
            {
                'name': user_name,
                'message': text,
                'datetime': date
            },
            {
                'name': self.NICKNAME,
                'message': response,
                'datetime': pytz.timezone(COUNTRY).localize(datetime.now()).isoformat(timespec="seconds")
            }
        ]
        if self.REMEMBER:
            try:
                await self.kurisu.add_memories(memory[0])  # User
                await self.kurisu.add_memories(memory[1])  # Kurisu
            except weaviate.SchemaValidationException:
                logging.error('Could Not add memories successfully')
                # print('Could Not add memories successfully')

        prompt.append({"role": "assistant", "content": response.strip()})
        self.chat_queue.pop(0)
        logging.info(prompt)
        logging.info(f"Generated response is worth of {self.kurisu.count_tokens()} tokens in {timeR} seconds")
        return response



    async def send_voice_binary(self, chat_id, context : ContextTypes.bot_data, binary_audio=None):
        if binary_audio is None:
            return

        await context.bot.send_chat_action(chat_id=chat_id,  action=ChatAction.RECORD_VOICE)
        await context.bot.send_voice(chat_id=chat_id, voice=binary_audio)


    async def send_voice_path(self, chat_id, context):  # DO NOT TOUCH, FIX THIS
        await context.bot.send_chat_action(chat_id=chat_id,  action=ChatAction.RECORD_VOICE)
        # audio_path = 'Audio\\with_rvc.wav'
        # ogg_path = 'Audio\\with_rvc.ogg'
        # convert_wav_to_ogg(audio_path, ogg_path)

        # with open(ogg_path, 'rb') as audio_file:
        #     await context.bot.send_voice(chat_idq=chat_id, audio=audio_file)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Sender`s data
        sender = update.message.from_user
        message: str = update.message.text
        print(message)
        datetimeU = update.message.date.isoformat()  # - format datetime to store in vdb
        message = emoji.replace_emoji(message, replace='').strip()
        # if message == 'voice':
        #     await self.send_voice_binary(chat_id=update.message.chat_id, context=context)
        #     return
        # if not message:
        #     return

        print(sender.full_name)

        if len(self.chat_queue) > 0:
            await update.message.reply_text("Wait a little bit, Kurisu is typing")
            return
        else:
            self.chat_queue.append({
                'from': self.CREATOR_USERNAME if self.CREATOR_ID == sender.id else f'{sender.full_name}',
                'message': message,
                'datetime': datetimeU
            })

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        response: str = await self.handle_response()

        if response is None:
            return
        # print(response)
        await update.message.reply_text(response)
        rand_value = random.random()
        print(rand_value)


        if self.VOICE and self.VOICE_CHANGE:
            start_time = time.time()
            response_in_jp = translate_text(response, 'ja')
            bin_voice = self.voicevox.generate_tts(response_in_jp, rvc=True)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info(f"Time taken: {elapsed_time} seconds")
            await self.send_voice_binary(update.message.chat_id, context, bin_voice)
        elif self.VOICE:
            start_time = time.time()
            response_in_jp = translate_text(response, 'ja')
            bin_voice = self.voicevox.generate_tts(response_in_jp)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info(f"Time taken: {elapsed_time} seconds")
            await self.send_voice_binary(update.message.chat_id, context, bin_voice)

        if not self.STICKERS:
            return

        if rand_value < 0.47:
            emotion, score = self.classifier(response)[0].values()
            sticker_id = random.choice(feelings_dict[emotion])
            await context.bot.send_sticker(update.effective_chat.id, sticker=sticker_id)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.WHISPER:
            return

        print('Got the users voice')

        sender = update.message.from_user
        # user_states = context.user_states
        datetimeU = update.message.date.isoformat()  # - format datetime to store in vdb

        voice_file = await context.bot.get_file(update.message.voice.file_id)

        print(f'got the voice {voice_file}')
        await voice_file.download_to_drive(self.AUDIO_DIR / self.VOICE_FILE)
        try:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
            response = transcribe(self.AUDIO_DIR / self.VOICE_FILE)
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
        if not reply_text:
            return
        if len(self.chat_queue) > 0:
            await update.message.reply_text("Wait a little bit, Kurisu is typing")
            return
        else:
            self.chat_queue.append({
                'from': self.CREATOR_USERNAME if self.CREATOR_ID == sender.id else f'{sender.full_name}',
                'message': reply_text,
                'datetime': datetimeU
            })

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        response: str = await self.handle_response()

        if response is None:
            return

        await update.message.reply_text(response)
        rand_value = random.random()
        print(rand_value)
        if rand_value < 0.45:
            emotion, score = self.classifier(response)[0].values()
            sticker_id = random.choice(feelings_dict[emotion])
            await context.bot.send_sticker(update.effective_chat.id, sticker=sticker_id)

    # Errors
    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f'error {context.error} from {update}')


bot_ready_event = threading.Event()


def start_bot():
    global bot, loop, bot_ready_event
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print('starting bot')
    bot = MyBot()
    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=pytz.timezone(COUNTRY))
    bot.app = (
        Application.builder()
        .token(TOKEN)
        .defaults(defaults)
        .build()
    )
    filter_users = TypeHandler(Update, bot.whitelist_user)
    bot.app.add_handler(filter_users, -1)
    # Commands
    bot.app.add_handler(CommandHandler('start', bot.start_command))
    bot.app.add_handler(CommandHandler('help', bot.help_command))
    bot.app.add_handler(CommandHandler('sticker', bot.send_sticker))

    # Messages
    bot.app.add_handler(MessageHandler(filters.TEXT, bot.handle_message))
    bot.app.add_handler(MessageHandler(filters.VOICE, bot.handle_voice))

    # Error
    bot.app.add_error_handler(bot.error)
    user_states = {}
    bot.app.context_types.context.user_states = user_states

    print('pooling')
    bot_ready_event.set()
    try:
        loop.run_until_complete(bot.app.run_polling(drop_pending_updates=True))
    except RuntimeError as e:
        if str(e) == 'Event loop is closed':
            print('Bot stopped gracefully')
        else:
            raise
    if loop is not None:
        loop.close()


def stop_bot():
    global loop, bot
    if loop is None or bot is None:
        return

    # noinspection PyUnresolvedReferences
    bot.kurisu.nullify()
    bot = None
    # noinspection PyUnresolvedReferences
    loop.stop()
    loop = None


def run_ai():
    global bot, bot_ready_event
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    bot_ready_event.wait()
    print(bot)

    time.sleep(1)

    print('\nStarted thread with bot telegram')
    return bot


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run_ai()