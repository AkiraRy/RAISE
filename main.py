import os

from config import SettingsManager, get_logger
from communication import TelegramInterface

logger = get_logger()

if __name__ == "__main__":
    token = os.getenv("TG_TOKEN")
    country = os.getenv("PLACE")
    CREATOR_ID = os.getenv('CREATOR_ID')
    settings_manager = SettingsManager().load_settings()
    bot = TelegramInterface(token, settings_manager.config.telegram)
    bot.start_in_thread()

    while True:
        pass
