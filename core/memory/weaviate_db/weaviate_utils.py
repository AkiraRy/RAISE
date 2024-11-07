import asyncio
import datetime
import json
import os.path

import weaviate
from weaviate.classes.query import MetadataQuery, Filter
from weaviate import exceptions
from config.settings import BACKUP_DIR
from core.memory import Memory, MemoryChain
from weaviate.classes.query import Sort
from core.memory.weaviate_db import WeaviateBase


# all backups would be stored at base/asses/db_backups
# TODO MAKE ASYNC WRITING OF BACKUP TO FILE LATER ON
async def backup(weaviate_db: WeaviateBase):
    # first we will make it not async
    name_backup = f"backup_{weaviate_db.config.class_name}_{datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.json"
    backup_path = BACKUP_DIR / name_backup
    try:
        print(f"Backup with name '{backup_path}' will be created")
        data = await retrieve_all_objects(weaviate_db)
        with open(backup_path, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(e)
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


async def load_from_backup(weaviate_db: WeaviateBase, file_name):
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


async def get_metadata(weaviate_db: WeaviateBase):
    meta_info = await weaviate_db.client.get_meta()
    print(json.dumps(meta_info, indent=4))


async def retrieve_all_objects(weaviate_db: WeaviateBase, limit=50):
    offset = 0
    all_objects = {}

    collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
    while True:
        response = await collection.query.fetch_objects(
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


def convert_response_to_mem_chain(response):
    sim_search = MemoryChain()
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


async def bm_25_search(weaviate_db: WeaviateBase, query: str):
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

        return convert_response_to_mem_chain(response)

    except Exception as e:
        print(e)


async def near_text_search(weaviate_db: WeaviateBase, query: str):
    try:
        filter_name = Filter.by_property("from").equal(weaviate_db.config.author_name)
        collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)

        response = await collection.query.near_text(
            query=query,
            filters=filter_name,
            limit=weaviate_db.config.limit,
            distance=weaviate_db.config.max_distance,
            return_metadata=MetadataQuery(distance=True)
        )

        return convert_response_to_mem_chain(response)
    except Exception as e:
        print(e)


async def hybrid_search(weaviate_db: WeaviateBase, query: str):
    try:
        filter_name = Filter.by_property("from").equal(weaviate_db.config.author_name)
        collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
        response = await collection.query.hybrid(
            query=query,
            filters=filter_name,
            limit=weaviate_db.config.limit,
            alpha=weaviate_db.config.alpha,
            query_properties=["message"],
            return_metadata=MetadataQuery(score=True)
        )

        return convert_response_to_mem_chain(response)
    except Exception as e:
        print(e)


async def delete_by_uuid(weaviate_db: WeaviateBase, uuid: str):
    assert isinstance(uuid, str) and uuid is not None, "Faulty value of uuid"
    collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
    await collection.data.delete_by_id(
        uuid
    )


async def get_by_uuid(weaviate_db: WeaviateBase, uuid: str):
    assert isinstance(uuid, str) and uuid is not None, "Faulty value of uuid"
    collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
    return await collection.query.fetch_object_by_id(uuid)
