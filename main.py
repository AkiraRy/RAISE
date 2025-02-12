import asyncio
import os
from enum import Enum
from config import SettingsManager, logger
from core import BrainHelper, WeaviateHelper
from communication import TelegramInterface, BaseInterface, DiscordInterface
from utils import start_server_handler, terminate_process  # add if checker, if those endpoints exists make a helper function in utils
import argparse


class Platform(Enum):
    DISCORD = "discord"
    TELEGRAM = "telegram"

    @classmethod
    def from_input(cls, value):
        value_map = {
            "d": cls.DISCORD,
            "t": cls.TELEGRAM,
            "discord": cls.DISCORD,
            "telegram": cls.TELEGRAM,
        }
        if value not in value_map:
            raise ValueError(f"Invalid choice: '{value}'. Choose from {', '.join(value_map.keys())}.")
        return value_map[value]


class AIAssistant:
    def __init__(self, settings_manager: SettingsManager, communication: BaseInterface, brain: BrainHelper, memory: WeaviateHelper):
        self.settings_manager = settings_manager
        self.communication = communication
        # self.communication_thread = None
        self.brain = brain
        self.memory = memory

    async def initialize(self):
        # Temporary fix
        if isinstance(self.communication, DiscordInterface):
            await self.communication.initialize()
        else:
            self.communication.initialize()

    async def start(self):
        await self.initialize()
        self.communication_thread = self.communication.start_in_thread()
        await asyncio.sleep(2)
        logger.info(f'[AIAssistant/start] Application is ready to use.')

    async def stop(self):
        # add here stopping of servers if necessary
        # self.memory.close()
        # self.brain.close()
        logger.info(f'[AIAssistant/stop] stopping the Application.')
        logger.info(f'[AIAssistant/stop] Application stopped successfully')


async def discord():
    # Settings, env values
    ds_token = os.getenv("DISCORD_TOKEN")
    settings_manager = SettingsManager().load_settings()
    weaviate_base_url = f'http://{settings_manager.config.weaviate.server_host}:{settings_manager.config.weaviate.server_port}'
    brain_base_url = f'http://{settings_manager.config.brain.server_host}:{settings_manager.config.brain.server_port}'

    # Modules
    discord_settings = settings_manager.config.discord
    brain_helper = BrainHelper(brain_base_url)
    memory_helper = WeaviateHelper(weaviate_base_url)

    # Communication
    ds_interface = DiscordInterface(
        token=ds_token,
        config=discord_settings,
        creator_username=settings_manager.config.brain.creator_name,
        brain=brain_helper
    )

    ai = AIAssistant(settings_manager, ds_interface, brain_helper, memory_helper)

    await ai.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    except asyncio.exceptions.CancelledError:
        pass
    finally:
        await ai.stop()


async def telegram():
    # Settings, env values
    telegram_token = os.getenv("TG_TOKEN")
    settings_manager = SettingsManager().load_settings()
    weaviate_base_url = f'http://{settings_manager.config.weaviate.server_host}:{settings_manager.config.weaviate.server_port}'  # add to config
    brain_base_url = f'http://{settings_manager.config.brain.server_host}:{settings_manager.config.brain.server_port}'

    # Modules
    telegram_settings = settings_manager.config.telegram
    brain_helper = BrainHelper(brain_base_url)
    memory_helper = WeaviateHelper(weaviate_base_url)

    tg_interface = TelegramInterface(
        token=telegram_token,
        config=telegram_settings,
        creator_username=settings_manager.config.brain.creator_name,
        brain=brain_helper
    )

    ai = AIAssistant(settings_manager, tg_interface, brain_helper, memory_helper)
    await ai.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    except asyncio.exceptions.CancelledError:
        pass
    finally:
        await ai.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Choose between Discord or Telegram method of communication between you "
                                                 "and model.")

    parser.add_argument(
        "-p", "--platform",
        choices=["d", "t", "discord", "telegram"],
        default="telegram",
        help="Specify the communication module to use. Use 'discord' or 'd' for Discord, 'telegram' or 't' for Telegram. "
             "Default is 'telegram'."
    )

    args = parser.parse_args()

    try:
        communication_module = Platform.from_input(args.platform)
    except ValueError as e:
        print(e)
        exit(1)

    try:
        process_server_weaviate, process_id = start_server_handler("backend.weaviate_server:app", 8000) # use config here
    except Exception as e:
        logger.error(f"Error starting server_handler: {e}")
        exit(1)

    try:
        process_server_brain, process_id = start_server_handler("backend.brain_server:app", 8001)
    except Exception as e:
        logger.error(f"Error starting brain_server: {e}")
        exit(1)

    try:
        if communication_module == Platform.DISCORD:
            asyncio.run(discord())
        elif communication_module == Platform.TELEGRAM:
            asyncio.run(telegram())
        else:
            raise RuntimeError("Undetected communication module")
    except KeyboardInterrupt:
        pass
    except asyncio.exceptions.CancelledError:
        pass

    terminate_process(process_server_weaviate)
    terminate_process(process_server_brain)
