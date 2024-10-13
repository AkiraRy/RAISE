import asyncio
import os
import sys
import threading
import time
import tkinter as tk

import uvicorn
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, ContextTypes

from core.plugin_manager import PluginManager
import config.settings as settings
from communication import TelegramInterface

logger = settings.logging.getLogger()


if __name__ == "__main__":
    token = os.getenv("TG_TOKEN")
    country = os.getenv("PLACE")
    CREATOR_ID = os.getenv('CREATOR_ID')

    config = {
        'CREATOR_ID': CREATOR_ID,
        "Country": country
    }

    bot = TelegramInterface(token, config)

    bot.start_in_thread()

    while True:
        pass
