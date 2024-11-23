import datetime
from typing import Optional, List
from httpx import AsyncClient  # HTTP requests
from . import Async_DB_Interface, logger, MemoryChain, Memory


# Weaviate Helper Class
class WeaviateHelper(Async_DB_Interface):
    async def connect(self) -> bool:
        try:
            logger.info(f'[WeaviateHelper/connect] Asking if Weaviate is still alive')
            response = await self.client.get(f"{self.base_url}/is_alive")
            if response.status_code == 200 and response.json().get("status") == "success":
                logger.info(f'[WeaviateHelper/connect] Weavite is still alive')
                return True
            logger.info(f'[WeaviateHelper/connect] Weavite is not alive')
            return False
        except Exception as e:
            print(f"Error checking /is_alive endpoint: {e}")
            return False

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = AsyncClient()

    async def add_memories(self, memory_chain: MemoryChain) -> bool:
        url = f"{self.base_url}/add_memories"
        try:

            memory_chain_json = convert_memory_chain_to_json(memory_chain)
            logger.info(f'[WeaviateHelper/add_memories] Sending a post request for memory adding.')
            response = await self.client.post(url, json={"memory_chain": memory_chain_json})
            if response.status_code == 200:
                logger.info(f'[WeaviateHelper/add_memories] Memories were added successfully')
                return True
            logger.error(f"[WeaviateHelper/add_memories] Failed to add memories with status {response.status_code}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"[WeaviateHelper/add_memories] Exception: {e}")
            return False

    async def get_context(self, query: str) -> Optional[MemoryChain]:
        url = f"{self.base_url}/get_context"
        try:
            logger.info(f'[WeaviateHelper/get_context] Sending a post request for memory adding.')
            response = await self.client.get(url,  params={"query": query})
            if response.status_code == 200:
                logger.info(f'[WeaviateHelper/get_context] Successfully got context for query {query}.')
                context_data = response.json().get("context", [])
                return convert_json_to_memory_chain(context_data)

            logger.error(f"[WeaviateHelper/get_context] Failed to get context with status {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"[WeaviateHelper/get_context] Exception: {e}")
            return None

    async def get_chat_memory(self, limit: int = 20) -> Optional[MemoryChain]:
        url = f"{self.base_url}/get_chat_memory"
        try:
            logger.info(f"[WeaviateHelper/get_chat_memory] Sending get request for chat memory with limit: {limit}")
            response = await self.client.get(url, params={"limit": limit})
            if response.status_code == 200:
                logger.info(
                    f"[WeaviateHelper/get_chat_memory] Successfully retrieved chat memories with")
                chat_history_data = response.json().get("chat_history", [])
                return convert_json_to_memory_chain(chat_history_data)
            logger.error(f"[WeaviateHelper/get_chat_memory] Failed to get chat memory with status {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"[WeaviateHelper/get_chat_memory] Exception: {e}")
            return None

    async def _shutdown_server(self) -> bool:
        url = f"{self.base_url}/shutdown"

        try:
            logger.info(f"[WeaviateHelper/_shutdown_server] Sending post request to shutdown weaviate server")
            response = await self.client.post(url)
            if response.status_code == 200:
                logger.info(
                    f"[WeaviateHelper/_shutdown_server] Successfully shutdown weaviate server")
                return True
            logger.error(f"[WeaviateHelper/_shutdown_server] Failed to shutdown server {response.status_code}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"[WeaviateHelper/_shutdown_server] Exception: {e}")
            return False

    async def close(self):
        logger.info(f"[WeaviateHelper/close] Trying to close fastapi server")
        did_shutdown = await self._shutdown_server()
        if not did_shutdown:
            logger.error(f"[WeaviateHelper/close] Couldn't close fastapiserver")
            return
        logger.info(f"[WeaviateHelper/close] Closed fastapi server")
        logger.info(f"[WeaviateHelper/close] Closing async client")
        await self.client.aclose()
        return did_shutdown


def convert_memory_chain_to_json(memory_chain: MemoryChain) -> List[dict]:
    logger.info(f'[convert_memory_chain_to_json] Converting memory chain to json')
    try:
        json_data = [
            {
                "from_name": memory.from_name,
                "message": memory.message,
                "time": memory.time.isoformat(),  # Convert datetime to string for JSON
                "distance": memory.distance,
                "certainty": memory.certainty,
                "score": memory.score,
            }
            for memory in memory_chain.memories
        ]
        return json_data
    except Exception as e:
        logger.error(f"[WeaviateHelper/convert_memory_chain_to_json] Error converting MemoryChain to JSON: {e}")
        return []


def convert_json_to_memory_chain(json_data: List[dict]) -> MemoryChain:
    logger.info(f'[convert_json_to_memory_chain] Converting json to memory chain ')
    try:
        memory_chain = MemoryChain()
        for memory_data in json_data:
            memory = Memory(
                from_name=memory_data["from_name"],
                message=memory_data["message"],
                time=datetime.datetime.fromisoformat(memory_data["time"]),
                distance=memory_data.get("distance"),
                certainty=memory_data.get("certainty"),
                score=memory_data.get("score"),
            )
            memory_chain.add_object(memory=memory)
        return memory_chain
    except Exception as e:
        logger.error(f"[WeaviateHelper/convert_json_to_memory_chain] Error converting JSON to MemoryChain: {e}")
        return MemoryChain()