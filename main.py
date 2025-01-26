import asyncio
import os
from enum import Enum

from config import SettingsManager, logger
from core import Brain, Model, PubSub, WeaviateHelper
from communication import TelegramInterface, BaseInterface, DiscordInterface
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
    def __init__(self, settings_manager: SettingsManager, communication: BaseInterface, brain: Brain):
        self.settings_manager = settings_manager
        self.communication = communication
        self.communication_thread = None
        self.brain = brain

    async def initialize(self):
        # Temporary fix
        if isinstance(self.communication, DiscordInterface):
            await self.communication.initialize()
        else:
            self.communication.initialize()

    async def start(self):
        await self.brain.start()
        await self.initialize()
        self.communication_thread = self.communication.start_in_thread()
        await asyncio.sleep(2)
        logger.info(f'[AIAssistant/start] Application is ready to use.')

    async def stop(self):
        logger.info(f'[AIAssistant/stop] stopping the Application.')
        self.brain.close()
        await self.brain.memory_manager.close()
        # self.communication.stop()
        logger.info(f'[AIAssistant/stop] Application stopped successfully')


async def discord():
    # Settings, env values
    ds_token = os.getenv("DISCORD_TOKEN")
    settings_manager = SettingsManager().load_settings()
    weaviate_base_url = 'http://127.0.0.1:8000'

    # Modules

    # Core
    weaviate_db = WeaviateHelper(weaviate_base_url)
    model = Model(settings_manager.config.llm)
    pubsub_system = PubSub(pooling_delay=0.1)
    brain = Brain(
            memory_manager=weaviate_db,
            model=model,
            config=settings_manager.config.brain,
            pubsub=pubsub_system,
            publish_to=settings_manager.config.pubsub.processed_message_topic,
            subscribe_to=settings_manager.config.pubsub.input_message_topic,
    )

    # Communication
    ds_interface = DiscordInterface(
        token=ds_token,
        config=settings_manager.config.discord,
        pubsub=pubsub_system,
        publish_to=settings_manager.config.pubsub.input_message_topic,
        subscribe_to=settings_manager.config.pubsub.processed_message_topic,
        creator_username=settings_manager.config.brain.creator_name
    )

    pubsub_system.start()
    ai = AIAssistant(settings_manager, ds_interface, brain)

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
        pubsub_system.stop()


async def telegram():
    # Settings, env values
    telegram_token = os.getenv("TG_TOKEN")
    settings_manager = SettingsManager().load_settings()
    weaviate_base_url = 'http://127.0.0.1:8000'

    # Modules
    weaviate_db = WeaviateHelper(weaviate_base_url)
    telegram_settings = settings_manager.config.telegram
    model = Model(settings_manager.config.llm)
    pubsub_system = PubSub(pooling_delay=0.1)
    brain = Brain(
        memory_manager=weaviate_db,
        model=model,
        config=settings_manager.config.brain,
        pubsub=pubsub_system,
        publish_to=settings_manager.config.pubsub.processed_message_topic,
        subscribe_to=settings_manager.config.pubsub.input_message_topic,
    )

    tg_interface = TelegramInterface(
        token=telegram_token,
        config=telegram_settings,
        pubsub=pubsub_system,
        publish_to=settings_manager.config.pubsub.input_message_topic,
        subscribe_to=settings_manager.config.pubsub.processed_message_topic,
        creator_username=settings_manager.config.brain.creator_name
    )

    pubsub_system.start()
    ai = AIAssistant(settings_manager, tg_interface, brain)
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
        pubsub_system.stop()


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
        exit(0)

    try:
        if communication_module == Platform.DISCORD:
            asyncio.run(discord())
        elif communication_module == Platform.TELEGRAM:
            asyncio.run(telegram())

        else:
            raise RuntimeError("Undetected cocmunication module")
    except KeyboardInterrupt:
        pass
    except asyncio.exceptions.CancelledError:
        pass
    