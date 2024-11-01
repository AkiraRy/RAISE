import asyncio
import datetime
import json
import os.path

import weaviate
from weaviate import exceptions
from config.settings import SettingsManager, BACKUP_DIR
from core.memory.weaviate_db.weaviate_db import Weaviate
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


async def main():
    wset = SettingsManager().load_single_module("weaviate")
    w_db = Weaviate(settings=wset)
    try:
        await w_db.connect_db()
        # asyncio.run(load_from_backup(w_db, "backup1.json"))
        all_objects = await retrieve_all_objects(w_db)
        # print(all_objects)
        # await backup(w_db)
        file_back = "backup_MemoryK_2024_11_02-00_01_19.json"
        await load_from_backup(w_db, file_back)
    finally:
        await w_db.client.close()


if __name__ == '__main__':
    asyncio.run(main())