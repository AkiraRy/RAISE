# TODO Here will be included setup for initialization of weaviate collection
# TODO Maybe make here a simple gui or cli app to configure everything connected with weaviate e.g ports and so on. Or we will do it somewhere else and initialize everything there
import asyncio

from config import SettingsManager
from core.memory.weaviate_db.weaviate_db import Weaviate


async def setup_main_collection():
    try:
        wset = SettingsManager().load_single_module("weaviate")
        w_db = Weaviate(wset)
        await w_db.client.connect()
        await create_collection(client=w_db.client, collection_name=wset.class_name)
    except AssertionError as e:
        print("Collection allready exists, will do nothing") # change to logs in future
    finally:
        if await w_db.client.is_live():
            await w_db.close()

if __name__ == '__main__':
    asyncio.run(main())
