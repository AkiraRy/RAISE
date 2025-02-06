from httpx import AsyncClient  # HTTP requests
from utils import Message_server
from config import logger


class BrainHelper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = AsyncClient()

    async def generate_response(self, message: Message_server) -> str:
        url = f"{self.base_url}/generate"

        try:
            data = message.dict()
            logger.info(f'[BrainHelper/generate_response] Sending a post request for response generation')
            response = await self.client.post(url, json=data, timeout=30)
            logger.debug(f"[BrainHelper/generate_response]  response: {response}")
            if response.status_code == 200:
                logger.info(f'[BrainHelper/generate_response] Response generated successfully')
                logger.debug(f'[BrainHelper/generate_response] Response {response.json()["message"]}')
                return response.json()['message']  # This is probably dangerous :smok:
            logger.error(f"[BrainHelper/generate_response] Failed to generated response {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"[BrainHelper/generate_response] Exception: {e}")
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
        """Close the AsyncClient session."""
        await self.client.aclose()