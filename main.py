import asyncio
import os
from config import SettingsManager, logger
from core import Weaviate, Async_DB_Interface, Brain, Model, PubSub, WeaviateHelper
from communication import TelegramInterface, BaseInterface, DiscordInterface


class AIAssistant:
    def __init__(self, settings_manager: SettingsManager, communication: BaseInterface, brain: Brain):
        self.settings_manager = settings_manager
        self.communication = communication
        self.communication_thread = None
        self.brain = brain

    async def start(self):
        await self.brain.start()
        await self.communication.initialize()
        self.communication_thread = self.communication.start_in_thread()
        await asyncio.sleep(1)
        logger.info(f'[AIAssistant/start] Application is ready to use.')

    async def stop(self):
        logger.info(f'[AIAssistant/stop] stopping the Application.')
        self.brain.close()
        await self.brain.memory_manager.close()
        logger.info(f'[AIAssistant/stop] Application stopped successfully')


async def main():
    token = os.getenv("DISCORD_TOKEN")
    settings_manager = SettingsManager().load_settings()
    weaviate_base_url = 'http://127.0.0.1:8000'
    weaviate_db = WeaviateHelper(weaviate_base_url)

    telegram_settings = settings_manager.config.telegram
    model = Model(settings_manager.config.llm)
    pubsub_system = PubSub(pooling_delay=0.1)
    brain = Brain(
        memory_manager=weaviate_db,
        # memory_manager=None,
        model=model,
        config=settings_manager.config.brain,
        pubsub=pubsub_system,
        publish_to=settings_manager.config.pubsub.processed_message_topic,
        subscribe_to=settings_manager.config.pubsub.input_message_topic,
    )

    # tg_interface = TelegramInterface(
    #     token=token,
    #     config=telegram_settings,
    #     pubsub=pubsub_system,
    #     publish_to=settings_manager.config.pubsub.input_message_topic,
    #     subscribe_to=settings_manager.config.pubsub.processed_message_topic,
    #     creator_username=settings_manager.config.brain.creator_name
    # )
    ds_interface = DiscordInterface(
        token=token,
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
    finally:
        await ai.stop()
        pubsub_system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
