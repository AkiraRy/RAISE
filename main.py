import asyncio
import os
from config import SettingsManager, logger
from core import Weaviate,  Async_DB_Interface, Brain, Model
from communication import TelegramInterface, BaseInterface
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)


class AIAssistant:
    def __init__(self,
                 settings_manager: SettingsManager,
                 communication: BaseInterface,
                 database: Async_DB_Interface,
                 brain: Brain,
                 ):
        self.settings_manager = settings_manager
        self.communication = communication
        self.communication_thread = None
        self.database = database
        self.brain = brain

    async def start(self):
        await self.database.connect()
        self.brain.load_model()
        self.communication_thread = self.communication.start_in_thread()

    async def stop(self):
        await self.database.close()
        self.brain.close()


async def main():
    token = os.getenv("TG_TOKEN")
    settings_manager = SettingsManager().load_settings()
    Weaviate_db = Weaviate(settings_manager.config.weaviate)
    stop_queue = asyncio.Queue()  # Shared stop queue

    telegram_settings = settings_manager.config.telegram
    model = Model(settings_manager.config.llm)

    brain = Brain(memory_manager=Weaviate_db,
                  model=model,
                  persona_path=settings_manager.config.persona,
                  user_name=telegram_settings.creator_username,
                  assistant_name=telegram_settings.bot_nickname
                  )
    print(brain.persona)

    tg_interface = TelegramInterface(token, telegram_settings, stop_queue)
    ai = AIAssistant(settings_manager, tg_interface, Weaviate_db, brain)

    await ai.start()

    async def monitor_stop():
        await stop_queue.get()  # This will block until the stop signal is received
        await ai.stop()

    try:
        # await stop_task
        await monitor_stop()
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        if await Weaviate_db.client.is_live():
            await ai.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted by user.")
