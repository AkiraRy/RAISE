import datetime
import json
import os.path
from typing import Optional

from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery, Filter, Sort
from weaviate import exceptions

from . import WeaviateBase, Memory, MemoryChain, BACKUP_DIR, logger


# all backups would be stored at base/asses/db_backups
# TODO MAKE ASYNC WRITING OF BACKUP TO FILE LATER ON
async def backup(weaviate_db: WeaviateBase):
    logger.info(f'[Weaviate_utils/backup] Started making a backup')

    # first we will make it not async
    name_backup = f"backup_{weaviate_db.config.class_name}_{datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.json"
    backup_path = BACKUP_DIR / name_backup
    try:
        logger.info(f"[Weaviate_utils/backup] Backup with name '{backup_path}' will be created")
        data = await retrieve_all_objects(weaviate_db)
        with open(backup_path, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        logger.error(f"[Weaviate_utils/backup] Couldn't make a backup, error: {e}")
    else:
        logger.info(f"[Weaviate_utils/backup] Backup was successfully created")
        return backup_path


def load_data_from_file(filename):
    logger.info(f'[Weaviate_utils/load_data_from_file] Started loading data from a file {filename}')

    try:
        with open(filename, "r", encoding='utf-8') as data:
            list_of_objects = json.load(data)
    except IOError:
        logger.error(f"[Weaviate_utils/load_data_from_file] Couldn't load file from backup '{filename}'")
        return None

    logger.info(f"[Weaviate_utils/load_data_from_file] Loaded data from backup '{filename}'")
    return list_of_objects


async def load_from_backup(weaviate_db: WeaviateBase, file_name):
    logger.info(f'[Weaviate_utils/load_from_backup] Started loading from a backup')

    full_path = BACKUP_DIR / file_name
    if not os.path.exists(full_path):
        logger.error(f"[Weaviate_utils/load_from_backup] There is no backup with this path: {full_path} ")
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
            logger.error(
                f'[Weaviate_utils/load_from_backup] This is already in memory\n{from_field}, {message_field}\n')
        except exceptions.SchemaValidationException:
            raise exceptions.SchemaValidationException
        else:
            logger.info(f'[Weaviate_utils/load_from_backup] Successfully added to memory, uuid: {uuid}')
    logger.info(f'[Weaviate_utils/load_from_backup] Successfully made a backup {full_path}')


async def get_metadata(weaviate_db: WeaviateBase):
    meta_info = await weaviate_db.client.get_meta()
    print(json.dumps(meta_info, indent=4))


async def retrieve_all_objects(weaviate_db: WeaviateBase, limit=50):
    logger.info(f'[Weaviate_utils/retrieve_all_objects] Started retrieving all objects from a database')

    offset = 0
    all_objects = {}
    try:
        collection = weaviate_db.client.collections.get(weaviate_db.config.class_name)
        while True:
            logger.info(f"[Weaviate_utils/retrieve_all_objects] Objects from {offset} to {offset + limit}")
            response = await collection.query.fetch_objects(
                sort=Sort.by_property(name="datetime", ascending=True),
                limit=limit,
                offset=offset
            )

            if not response.objects:
                logger.info(f"[Weaviate_utils/retrieve_all_objects] no objects at {offset} to {offset + limit}")
                break

            for o in response.objects:
                data = {
                    "from": o.properties["from"],
                    "message": o.properties["message"],
                    "datetime": o.properties["datetime"].isoformat(),
                }
                all_objects[str(o.uuid)] = data
                logger.info(f"[Weaviate_utils/retrieve_all_objects] adding object uuid({str(o.uuid)}) {data}")

            offset += limit
            if len(response.objects) < limit:
                logger.info(f"[Weaviate_utils/retrieve_all_objects] There is less objects than {limit}, escaping loop")
                break

        logger.info(f"[Weaviate_utils/retrieve_all_objects] Successfully returned all objects {offset}")
        return all_objects
    except Exception as e:
        logger.error(f"[Weaviate_utils/retrieve_all_objects] got an unexpected error {e}")


def convert_response_to_mem_chain(response, algo_name: Optional[str] = None) -> Optional[MemoryChain]:
    if not response:
        logger.warning(
            f"[Weaviate_utils.py/convert_response_to_mem_chain] There are no similar elements in the response")
        return None

    sim_search = MemoryChain()
    try:
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
    except Exception as e:
        logger.error(f"[Weaviate_utils.py/convert_response_to_mem_chain] got an unexpected error {e}")
        return None

    if algo_name:
        logger.info(f"[Weaviate_utils.py/convert_response_to_mem_chain] Successfully made a memory chain of similar"
                    f" messages using {algo_name}")
    else:
        logger.info(f"[Weaviate_utils.py/convert_response_to_mem_chain] Successfully made a memory chain")
    return sim_search


async def bm_25_search(weaviate_db: WeaviateBase, query: str) -> Optional[MemoryChain]:
    logger.info(f"[Weaviate_utils/bm_25_search] Starting bm25 keyword similarity search, for query {query}")

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

        return convert_response_to_mem_chain(response, "bm25")
    except Exception as e:
        logger.error(f"[Weaviate_utils/bm_25_search] got an unexpected error {e}")


async def near_text_search(weaviate_db: WeaviateBase, query: str) -> Optional[MemoryChain]:
    logger.info(f"[Weaviate_utils/near_text_search] Starting near text vector similarity search, for query {query}")

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

        return convert_response_to_mem_chain(response, "near text")
    except Exception as e:
        logger.error(f"[Weaviate_utils/near_text_search] got an unexpected error {e}")


async def hybrid_search(weaviate_db: WeaviateBase, query: str) -> Optional[MemoryChain]:
    logger.info(f"[Weaviate_utils/hybrid_search] Starting hybrid similarity search, for query {query}")

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

        return convert_response_to_mem_chain(response, "hybrid")
    except Exception as e:
        logger.error(f"[Weaviate_utils/hybrid_search] got an unexpected error {e}")


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


async def check_if_exists(weaviate_db: WeaviateBase, collection_name: str):
    assert await weaviate_db.client.is_live(), "No connection with client."
    return await weaviate_db.client.collections.exists(collection_name)


async def create_collection(weaviate_db: WeaviateBase, collection_name: str):
    assert not await check_if_exists(weaviate_db,
                                     collection_name), f"Collection({collection_name}) with given name already exists."
    new_collection_scheme = await weaviate_db.client.collections.create(
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
