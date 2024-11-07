import asyncio
from enum import Enum
from typing import Optional

from weaviate.connect import ConnectionParams
from core.memory import Memory, SimilaritySearch
from core.memory.weaviate_db import WeaviateBase
from core.memory.weaviate_db.weaviate_utils import bm_25_search, near_text_search, hybrid_search
from weaviate import WeaviateAsyncClient, exceptions
from config.settings import WeaviateSettings
# from weaviate.exceptions import *

import logging
logger = logging.getLogger("bot")

similarity_search = {
    "hybrid": hybrid_search,
    "bm_25": bm_25_search,
    'near_text': near_text_search
}


# TODO add here in exceptions to check if we somehow became unalive and if so try to connect again
class Weaviate(WeaviateBase):
    def __init__(self, settings: WeaviateSettings):
        super().__init__(settings)

    async def add_memories(self, memory: Memory):
        if not self.client or not await self.client.is_live():
            logger.error(f"[Weaviate/add_memories] Connection is closed. Cannot add memories")
            return

        collection = self.client.collections.get(self.config.class_name)
        try:
            uuid = await collection.data.insert({
                "from": memory.from_name,
                "message": memory.message,
                "datetime": memory.time
            })
        except exceptions.UnexpectedStatusCodeError as e:
            logger.error(f"[Weaviate/add_memories] Couldn't add data, most likely because there is memory in db with same parameters")
            return None
        else:
            logger.info(f"[Weaviate/add_memories] Memory added successfully {uuid}")

    async def get_context(self, query: str) -> Optional[SimilaritySearch]:
        # returns n similar messages texted by user to the query
        if not self.client or not await self.client.is_live():
            logger.error(f"[Weaviate/get_context] Connection is closed. Cannot get context")
            return None

        sim_search_function = similarity_search.get(self.config.sim_search_type, hybrid_search)
        return await sim_search_function(self, query)

    async def get_chat_memory(self):
        # returns last n messages, n counts for both the user and ai
        pass

    async def close(self):
        if self.client and await self.client.is_live():
            await self.client.close()
            logger.info(f"[Weaviate/close] Connection is closed successfully.")
            return
        logger.warning(f"[Weaviate/close] Cannot close connection, client doesn't exists")

    async def connect(self):
        max_retries = self.config.max_retries
        retry_delay = self.config.retry_delay
        final_err_str = "Failed to connect to Weaviate server after multiple attempts"
        err_str = "[Weaviate/connect_db] Failed to connect to Weaviate server: {e}"

        for retry in range(max_retries):
            try:
                conn_params = ConnectionParams.from_params(
                    http_host=self.config.http_host,
                    http_port=self.config.http_port,
                    http_secure=self.config.http_secure,
                    grpc_host=self.config.grpc_host,
                    grpc_port=self.config.grpc_port,
                    grpc_secure=self.config.grpc_secure
                )

                self.client = WeaviateAsyncClient(connection_params=conn_params)
                await self.client.connect()
                logger.info(f"[Weaviate/connect_db] Successfully connected to Async version of Weaviate")
                return 0
            except Exception as e:  # should fix this later proly
                if self.client:
                    await self.client.close()
                logger.error(err_str.format(e=str(e)))

            logger.error(f"[Weaviate/connect_db] Retrying connection in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)

        logger.error(f"[Weaviate/connect_db] {final_err_str}")
        # raise weaviate.WeaviateStartUpError(final_err_str)
        return -1
