import asyncio
from weaviate.connect import ConnectionParams
from core.memory import Async_DB_Interface
from weaviate import WeaviateAsyncClient
from config.settings import WeaviateSettings
# from weaviate.exceptions import *

import logging
logger = logging.getLogger("bot")


class Weaviate(Async_DB_Interface):
    async def add_memories(self, *args, **kwargs):
        pass

    async def get_context(self, *args, **kwargs):
        pass

    async def get_chat_memory(self):
        pass

    async def close(self):
        if self.client and await self.client.is_live():
            await self.client.close()
            logger.info(f"[Weaviate/close] Connection is closed successfully.")
            return
        logger.warning(f"[Weaviate/close] Cannot close connection, client doesn't exists")

    def __init__(self, settings: WeaviateSettings):
        self.config: WeaviateSettings = settings
        self.client: WeaviateAsyncClient | None = None

    async def connect_db(self):
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

    def add_data(self, *args, **kwargs):
        pass

    def retrieve(self, *args, **kwargs):
        pass
