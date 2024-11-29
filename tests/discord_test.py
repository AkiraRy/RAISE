import asyncio
import os

from config import SettingsManager
from communication import DiscordInterface
from core import PubSub


async def main():
    settings_manager = SettingsManager().load_settings()
    pubsub_system = PubSub(pooling_delay=0.1)

    token = os.getenv("DISCORD_TOKEN")
    ds_interface = DiscordInterface(
        token=token,
        config=settings_manager.config.discord,
        pubsub=pubsub_system,
        publish_to=settings_manager.config.pubsub.input_message_topic,
        subscribe_to=settings_manager.config.pubsub.processed_message_topic,
        creator_username=settings_manager.config.brain.creator_name
    )
    pubsub_system.start()
    await ds_interface.initialize()
    ds_thread = ds_interface.start_in_thread()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted by user.")
        ds_thread.join()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


