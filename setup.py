import asyncio

from config import SettingsManager, logger
from core import Weaviate, create_collection
from core.brain.download_model import model_download


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


def download_llm():
    settings = SettingsManager().load_settings()
    llm_settings = settings.config.llm

    model_download(llm_settings)


if __name__ == '__main__':
    asyncio.run(setup_main_collection_weaviate())
    download_llm()