import asyncio
from config.settings import WeaviateSettings
from core.memory.weaviate_db import Weaviate


async def main():
    wset = WeaviateSettings()
    w_db = Weaviate(wset)
    res = await w_db.connect_db()
    print(res)
    assert res == 0, "Should be 0, otherwise didn't connect successfully"
    await w_db.close()


if __name__ == '__main__':
    asyncio.run(main())
