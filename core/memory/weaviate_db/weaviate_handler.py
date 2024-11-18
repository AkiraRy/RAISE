import datetime
from typing import Optional, List
from httpx import AsyncClient  # HTTP requests
from . import Async_DB_Interface, logger, MemoryChain, Memory

# Weaviate Helper Class
class WeaviateHelper(Async_DB_Interface):
    async def connect(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/is_alive")
            if response.status_code == 200 and response.json().get("status") == "success":
                return True
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

            response = await self.client.post(url, json={"memory_chain": memory_chain_json})
            if response.status_code == 200:
                return True
            logger.error(f"[WeaviateHelper/add_memories] Failed with status {response.status_code}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"[WeaviateHelper/add_memories] Exception: {e}")
            return False

    async def get_context(self, query: str) -> Optional[MemoryChain]:
        url = f"{self.base_url}/get_context"
        try:
            response = await self.client.post(url, json={"query": query})
            if response.status_code == 200:
                context_data = response.json().get("context", [])
                return convert_json_to_memory_chain(context_data)

            logger.error(f"[WeaviateHelper/get_context] Failed with status {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"[WeaviateHelper/get_context] Exception: {e}")
            return None

    async def get_chat_memory(self, limit: int = 20) -> Optional[MemoryChain]:
        url = f"{self.base_url}/get_chat_memory"
        try:
            response = await self.client.get(url, params={"limit": limit})
            if response.status_code == 200:
                chat_history_data = response.json().get("chat_history", [])
                return convert_json_to_memory_chain(chat_history_data)
            logger.error(f"[WeaviateHelper/get_chat_memory] Failed with status {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"[WeaviateHelper/get_chat_memory] Exception: {e}")
            return None

    async def close(self):
        await self.client.aclose()


def convert_memory_chain_to_json(memory_chain: MemoryChain) -> List[dict]:
    """
    Converts a MemoryChain object into a JSON-serializable format (list of dicts).
    """
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
    """
    Converts a JSON response (list of dicts) into a MemoryChain object.
    """
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