# TODO Here will be included setup for initialization of weaviate collection
# TODO Maybe make here a simple gui or cli app to configure everything connected with weaviate e.g ports and so on. Or we will do it somewhere else and initialize everything there
import asyncio

from config import SettingsManager, logger
from core import Weaviate, create_collection


async def setup_main_collection_weaviate():
    try:
        wset = SettingsManager().load_single_module("weaviate")
        w_db = Weaviate(wset)
        await w_db.client.connect()
        await create_collection(weaviate_db=w_db, collection_name=w_db.config.class_name)
    except AssertionError as e:
        logger.error(f"[setup/WeaviateSettings] Collection {w_db.config.class_name} already exists, will do nothing")
    finally:
        if await w_db.client.is_live():
            await w_db.close()

if __name__ == '__main__':
    asyncio.run(setup_main_collection_weaviate())
