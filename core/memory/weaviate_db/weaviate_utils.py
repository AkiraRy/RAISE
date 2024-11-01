import asyncio
import json
import os.path

import weaviate
from weaviate import exceptions

from config.settings import SettingsManager, WeaviateSettings, BACKUP_DIR
from core.memory.weaviate_db.weaviate_db import Weaviate
# all backups would be stored at base/asses/db_backups


# TODO MAKE WRITING A BACKUP ASYNC LATER ON
async def backup():
    pass


def load_data_from_file(filename):
    try:
        with open(filename, "r", encoding='utf-8') as data:
            list_of_objects = json.load(data)
    except IOError:
        print(f"Couldn't load file from backup '{filename}'")
        return None
    print(f"Loaded data from backup '{filename}'")
    return list_of_objects


async def load_from_backup(weaviate_settings: WeaviateSettings, file_name):
    full_path = BACKUP_DIR / file_name
    if not os.path.exists(full_path):
        print(f"There is no backup with this path: {full_path} ")
        return -1

    data = load_data_from_file(full_path)

    if not data:
        return -1

    try:
        w_db = Weaviate(weaviate_settings)
        await w_db.connect_db()

        if not await w_db.client.is_live():
            print("couldnt connect to db")
            return -1

        collection = w_db.client.collections.get(weaviate_settings.class_name)
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
    finally:
        if await w_db.client.is_live():
            await w_db.close()


async def get_metadata(weaviate_settings: WeaviateSettings):
    try:
        w_db = Weaviate(weaviate_settings)
        await w_db.connect_db()
        meta_info = await w_db.client.get_meta()
        print(json.dumps(meta_info, indent=4))
    finally:
        if await w_db.client.is_live():
            await w_db.close()


async def read_all_data(weaviate_settings: WeaviateSettings):

    try:
        w_db = Weaviate(weaviate_settings)
        await w_db.connect_db()

        if not await w_db.client.is_live():
            print("couldnt connect to db")
            return -1
        counter = 0
        collection = w_db.client.collections.get(weaviate_settings.class_name)
        async for item in collection.iterator():
            print(item.uuid, item.properties)
            counter+=1
        print(counter)
    finally:
        if await w_db.client.is_live():
            await w_db.close()


if __name__ == '__main__':
    wset = SettingsManager().load_single_module("weaviate")
    # asyncio.run(load_from_backup(wset, "backup1.json"))
    asyncio.run(read_all_data(wset))
