import json
import random

async def getSticker(stickerPack_name, emoji):
    with open("stickerset.json", "r") as json_file:
        data = json.load(json_file)

    if stickerPack_name in data:
        if emoji in data[stickerPack_name]:
            my_emojiList = data[stickerPack_name][emoji][0]
            return my_emojiList[random.randint(0, len(my_emojiList) - 1)]

        else:
            print("no emoji")
            return None

    return None


async def add_stickerInfo(sticker_name: str, stickers_info):
    # Read the existing data from the JSON file
    existing_data = {}
    try:
        with open("stickerset.json", "r") as json_file:
            try:
                existing_data = json.load(json_file)
            except json.JSONDecodeError:
                existing_data = {}
    except FileNotFoundError:
        pass
    # Update the existing data with the new data
    for emoji, file_id in stickers_info.items():
        if emoji in existing_data.get(sticker_name, {}):
            # If the emoji already exists, append the new file ID to the existing list
            existing_data[sticker_name][emoji].append(file_id)
        else:
            # If the emoji doesn't exist, create a new list with the file ID
            existing_data.setdefault(sticker_name, {})[emoji] = [file_id]
    # Write the updated data to the JSON file
    with open("stickerset.json", "w+") as json_file:
        json.dump(existing_data, json_file, indent=4)


async def checkStickers(sticker_name: str):
    with open("stickerset.json", "r") as json_file:
        try:
            data = json.load(json_file)
        except json.JSONDecodeError:
            data = {}
    return sticker_name in data
