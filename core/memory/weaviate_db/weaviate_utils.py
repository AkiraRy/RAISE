import asyncio
import datetime
import json
import os.path

import weaviate
from weaviate.classes.query import MetadataQuery, Filter
from weaviate import exceptions
from config.settings import SettingsManager, BACKUP_DIR
from core.memory.weaviate_db.weaviate_db import Weaviate
from core.memory import Memory, SimilaritySearch
from weaviate.classes.query import Sort


# all backups would be stored at base/asses/db_backups
# TODO MAKE ASYNC WRITING OF BACKUP TO FILE LATER ON
async def backup(weaviate_db: Weaviate):
    # first we will make it not async
    name_backup = f"backup_{weaviate_db.config.class_name}_{datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.json"
    backup_path = BACKUP_DIR / name_backup
    try:
        print(f"Backup with name '{backup_path}' will be created")
        data = await retrieve_all_objects(weaviate_db)
        with open(backup_path, 'w') as file:
            json.dump(data, file, indent=4)
    except:
        pass
    else:
        print(f"Backup was successfully created")
        return backup_path


def load_data_from_file(filename):
    try:
        with open(filename, "r", encoding='utf-8') as data:
            list_of_objects = json.load(data)
    except IOError:
        print(f"Couldn't load file from backup '{filename}'")
        return None
    print(f"Loaded data from backup '{filename}'")
    return list_of_objects


async def load_from_backup(weaviate_db: Weaviate, file_name):
    full_path = BACKUP_DIR / file_name
    if not os.path.exists(full_path):
        print(f"There is no backup with this path: {full_path} ")
        return -1

    data = load_data_from_file(full_path)

    if not data:
        return -1

    collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
    for id, message_data in data.items():
        from_field = message_data['from']
        message_field = message_data['message']
        datetime_field = message_data['datetime']
        try:
            uuid = await collection.data.insert({
                "from": from_field,
                "message": message_field,
                "datetime": datetime_field
            })
        except exceptions.ObjectAlreadyExistsException:
            print(f'This is already in memory\n{from_field}, {message_field}\n')
        except weaviate.SchemaValidationException:
            raise exceptions.SchemaValidationException
        else:
            print(f'Successfully added to memory, uuid: {uuid}')


async def get_metadata(weaviate_db: Weaviate):
    meta_info = await weaviate_db.client.get_meta()
    print(json.dumps(meta_info, indent=4))


async def retrieve_all_objects(weaviate_db: Weaviate, limit=50):
    offset = 0
    all_objects = {}

    article = weaviate_db.client.collections.get(weaviate_db.config.class_name)
    while True:
        response = await article.query.fetch_objects(
            sort=Sort.by_property(name="datetime", ascending=True),
            limit=limit,
            offset=offset
        )

        if not response.objects:
            break

        for o in response.objects:
            data = {
                "from": o.properties["from"],
                "message": o.properties["message"],
                "datetime": o.properties["datetime"].isoformat(),
            }
            all_objects[str(o.uuid)] = data

        offset += limit
        if len(response.objects) < limit:
            break

    return all_objects


def convert_response_to_sim_class(response):
    sim_search = SimilaritySearch()
    # return response.objects
    for o in response.objects:
        from_name = o.properties["from"]
        message = o.properties["message"]
        time = o.properties["datetime"]
        distance = o.metadata.distance
        certainty = o.metadata.certainty
        score = o.metadata.score

        memory = Memory(from_name=from_name, message=message, time=time, distance=distance, certainty=certainty,
                        score=score)
        # sim_search.add_object(from_name=from_name,message=message,time=time,distance=distance,certainty=certainty,score=score)
        sim_search.add_object(memory=memory)
    return sim_search


async def bm_25_search(weaviate_db: Weaviate, query: str):
    try:
        filter_name = Filter.by_property("from").equal(weaviate_db.config.author_name)
        collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
        response = await collection.query.bm25(
            query=query,
            query_properties=["message"],
            filters=filter_name,
            limit=weaviate_db.config.limit,
            return_metadata=MetadataQuery(score=True)
        )

        return convert_response_to_sim_class(response)

    except Exception as e:
        print(e)


async def delete_by_uuid(weaviate_db: Weaviate, uuid: str):
    assert isinstance(uuid, str) and uuid is not None, "Faulty value of uuid"
    collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
    await collection.data.delete_by_id(
        uuid
    )


async def get_by_uuid(weaviate_db: Weaviate, uuid: str):
    assert isinstance(uuid, str) and uuid is not None, "Faulty value of uuid"
    collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
    return await collection.query.fetch_object_by_id(uuid)


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
        sim_search = await bm_25_search(w_db, "JLPT")
        print(sim_search)
    finally:
        await w_db.close()


if __name__ == '__main__':
    asyncio.run(test())
