# TODO Here will be included setup for initialization of weaviate collection
# TODO Maybe make here a simple gui or cli app to configure everything connected with weaviate e.g ports and so on. Or we will do it somewhere else and initialize everything there
import asyncio

from weaviate import WeaviateAsyncClient
from weaviate.classes.config import Configure, Property, DataType
from config.settings import SettingsManager
from core.memory.weaviate_db.weaviate_db import Weaviate


# take out to utils
async def check_if_exists(client: WeaviateAsyncClient, collection_name: str):
    assert await client.is_live(), "No connection with client."
    return await client.collections.exists(collection_name)


# take this to config file as well in future
async def create_collection(client: WeaviateAsyncClient, collection_name: str):
    assert not await check_if_exists(client, collection_name), f"Collection({collection_name}) with given name already exists."
    new_collection_scheme = await client.collections.create(
        name=collection_name,
        description="Message from Memory",
        vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
        properties=[
            Property(name="from", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="message", data_type=DataType.TEXT),
            Property(name="datetime", data_type=DataType.DATE, skip_vectorization=True)
        ],
    )

    return await new_collection_scheme.config.get()


async def main():
    global w_db
    try:
        wset = SettingsManager().load_single_module("weaviate")
        w_db = Weaviate(wset)
        await w_db.connect_db()
        await create_collection(client=w_db.client, collection_name=wset.class_name)
    except AssertionError as e:
        print("Collection allready exists, will do nothing") # change to logs in future
    finally:
        if await w_db.client.is_live():
            await w_db.close()

if __name__ == '__main__':
    asyncio.run(main())
