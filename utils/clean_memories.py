import asyncio

from core import Weaviate, delete_by_uuid
from config import SettingsManager, logger


async def check_check_for_deletion():
    try:
        settings_manager = SettingsManager().load_settings()
        weaviate_db = Weaviate(settings_manager.config.weaviate)
        await weaviate_db.connect()
        mem = await weaviate_db.get_chat_memory()
        for m in mem.memories:
            print(m)
    finally:
        await weaviate_db.close()

async def main():
    memories_to_delete = [
        '359a2a4d-a90d-4a6e-b554-0a8eb46a22de',
        '8c427578-3ed9-48cd-b7b3-78db5922818f',
        '8a81b5e1-4c4e-43e5-8389-0df71801bf6d',
        '2dc02892-6444-4f69-8334-f76b742ab1c7',
        '04d67d02-ac6b-4c5c-b5de-c71ded302451',
        '3ebbca18-76e7-4633-9614-3d5882b2b32e'
    ]
    try:
        settings_manager = SettingsManager().load_settings()
        weaviate_db = Weaviate(settings_manager.config.weaviate)
        await weaviate_db.connect()
        for uuid in memories_to_delete:
            logger.info(f"Deleting uuid({uuid})")
            await delete_by_uuid(weaviate_db, uuid)
    finally:
        await weaviate_db.close()

if __name__ == '__main__':
    asyncio.run(check_check_for_deletion())