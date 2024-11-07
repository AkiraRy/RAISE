import asyncio

from config.settings import SettingsManager
from core.memory.weaviate_db.weaviate_db import Weaviate
from core.memory.weaviate_db.setup import create_collection


async def connection_test():
    wset = SettingsManager().load_single_module("weaviate")
    w_db = Weaviate(wset)
    res = await w_db.connect()
    assert res == 0, "Should be 0, otherwise didn't connect successfully"
    await w_db.close()


async def retrieve_collection_test():
    try:
        wset = SettingsManager().load_single_module("weaviate")
        w_db = Weaviate(wset)
        res = await w_db.connect()
        assert await w_db.client.collections.exists(wset.class_name), f"Collection {wset.class_name} doesn't exists."
    finally:
        if await w_db.client.is_live():
            await w_db.close()


async def create_collection_test():
    try:
        wset = SettingsManager().load_single_module("weaviate")
        w_db = Weaviate(wset)
        await w_db.connect()
        # todo add here if exists to ignore the test 
        await create_collection(w_db.client, wset.class_name)
        assert w_db.client.collections.exists(wset.class_name),  f"Collection {wset.class_name} doesn't exists."
    except AssertionError as e:
        pass
    finally:
        await w_db.client.close()


async def test():
    wset = SettingsManager().load_single_module("weaviate")
    w_db = Weaviate(settings=wset)
    try:
        await w_db.connect()
        # asyncio.run(load_from_backup(w_db, "backup1.json"))
        # all_objects = await retrieve_all_objects(w_db)
        # print(all_objects)
        # await backup(w_db)
        # file_back = "backup_MemoryK_2024_11_02-00_01_19.json"
        # await load_from_backup(w_db, file_back)
        # uuid = "1b825cd3-a563-4e84-8ba5-78cd6eadb533"
        # print(await get_by_uuid(w_db, uuid))
        # query = "eat before exam"
        # sim_search = await bm_25_search(w_db, query)
        # print(sim_search)
        # sim_search = await near_text_search(w_db, query)
        # print(sim_search)
        # sim_search = await hybrid_search(w_db, query)
        # print(sim_search)
        # search_fun = await w_db.get_context('JLPT')
        # print(search_fun)

        # chat_memory = await w_db.get_chat_memory()
        # for memory in chat_memory.memories:
        #     print(memory.message)
        #     print(memory.time)
    finally:
        await w_db.close()


if __name__ == '__main__':
    asyncio.run(test())
    # asyncio.run(connection_test())
#     asyncio.run(retrieve_collection_test())
#     asyncio.run(create_collection_test())

