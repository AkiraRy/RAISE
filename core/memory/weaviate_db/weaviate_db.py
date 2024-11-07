import asyncio
from typing import Optional

from config.settings import WeaviateSettings
from core.memory import Memory, MemoryChain
from core.memory.weaviate_db.weaviate_utils import bm_25_search, near_text_search, hybrid_search, convert_response_to_mem_chain
from core.memory.weaviate_db import WeaviateBase
from weaviate import WeaviateAsyncClient, exceptions
from weaviate.classes.query import Sort
from weaviate.connect import ConnectionParams
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

    async def add_memories(self, memory: Memory) -> int:
        logger.error(f"[Weaviate/add_memories] Starting to add memories {memory}")

        if not self.client or not await self.client.is_live():
            logger.error(f"[Weaviate/add_memories] Connection is closed. Cannot add memories")
            return -1

        collection = self.client.collections.get(self.config.class_name)
        try:
            uuid = await collection.data.insert({
                "from": memory.from_name,
                "message": memory.message,
                "datetime": memory.time
            })
        except exceptions.UnexpectedStatusCodeError as e:
            logger.error(f"[Weaviate/add_memories] Couldn't add data, most likely because there is memory in db with same parameters")
            return -1
        else:
            logger.info(f"[Weaviate/add_memories] Memory added successfully {uuid}")
            return 0

    async def get_context(self, query: str) -> Optional[MemoryChain]:
        logger.info(f"[Weaviate/get_chat_memory] getting context(sim_search) for {query}")
        # returns n similar messages texted by user to the query
        if not self.client or not await self.client.is_live():
            logger.error(f"[Weaviate/get_context] Connection is closed. Cannot get context")
            return None

        sim_search_function = similarity_search.get(self.config.sim_search_type, hybrid_search)
        memory_chain = await sim_search_function(self, query)

        if not memory_chain:
            logger.info(f"[Weaviate/get_chat_memory] There is no similar messages to {query}")

        logger.info(f"[Weaviate/get_chat_memory] Successfully got context for query {query}")
        return memory_chain

    async def get_chat_memory(self, limit_messages=20) -> Optional[MemoryChain]:
        # returns last n messages, n counts for both the user and an AI
        logger.info(f"[Weaviate/get_chat_memory] getting chat history for {limit_messages} messages")
        try:
            collection = self.client.collections.get(self.config.class_name)
            response = await collection.query.fetch_objects(
                sort=Sort.by_property(name="datetime", ascending=False),
                limit=limit_messages,
            )
        except Exception as e:
            logger.info(f"[Weaviate/get_chat_memory] Got an error {e}")
            return None

        mem_chain = convert_response_to_mem_chain(response)
        mem_chain.memories.reverse()  # chat order
        logger.info(f"[Weaviate/get_chat_memory] Successfully retrieved chat history for {limit_messages} messages")
        return mem_chain

    async def close(self) -> None:
        if self.client and await self.client.is_live():
            await self.client.close()
            logger.info(f"[Weaviate/close] Connection is closed successfully.")
            return
        logger.warning(f"[Weaviate/close] Cannot close connection, client doesn't exists")

    async def connect(self) -> int:
        if self.client and await self.client.is_live():
            logger.warning(f"[Weaviate/connect] Already established connection")
            return 0

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
