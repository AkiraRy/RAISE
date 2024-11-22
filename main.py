import asyncio
import os
from config import SettingsManager, logger
from core import Weaviate, Async_DB_Interface, Brain, Model, PubSub, WeaviateHelper
from communication import TelegramInterface, BaseInterface


class AIAssistant:
    def __init__(self, settings_manager: SettingsManager, communication: BaseInterface, brain: Brain):
        self.settings_manager = settings_manager
        self.communication = communication
        self.communication_thread = None
        self.brain = brain

    async def start(self):
        await self.brain.start()
        self.communication_thread = self.communication.start_in_thread()
        await asyncio.sleep(1)
        logger.info(f'[AIAssistant/start] Application is ready to use.')

    async def stop(self):
        logger.info(f'[AIAssistant/stop] stopping the Application.')
        self.brain.close()
        await self.brain.memory_manager.close()
        logger.info(f'[AIAssistant/stop] Application stopped successfully')


async def main():
    token = os.getenv("TG_TOKEN")
    settings_manager = SettingsManager().load_settings()
    weaviate_base_url = 'http://127.0.0.1:8000'
    weaviate_db = WeaviateHelper(weaviate_base_url)

    telegram_settings = settings_manager.config.telegram
    model = Model(settings_manager.config.llm)
    pubsub_system = PubSub(pooling_delay=0.1)
    brain = Brain(
        memory_manager=weaviate_db,
        model=model,
        persona_path=settings_manager.config.persona,
        user_name=telegram_settings.creator_username,
        assistant_name=telegram_settings.bot_nickname,
        pubsub=pubsub_system,
        publish_to=settings_manager.config.pubsub.processed_message_topic,
        subscribe_to=settings_manager.config.pubsub.input_message_topic,
        save_memories=settings_manager.config.save_memories,
        use_memories=settings_manager.config.use_memories,
        add_context=settings_manager.config.add_context
    )

    tg_interface = TelegramInterface(
        token=token,
        config=telegram_settings,
        pubsub=pubsub_system,
        publish_to=settings_manager.config.pubsub.input_message_topic,
        subscribe_to=settings_manager.config.pubsub.processed_message_topic
    )

    pubsub_system.start()
    ai = AIAssistant(settings_manager, tg_interface, brain)

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
