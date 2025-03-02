import datetime
from typing import Optional, List
from httpx import AsyncClient  # HTTP requests
from config import logger  # change to main logger later


class PMHelper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = AsyncClient()

    async def tts(self, text: str) -> bytes:  # this is wrong
        # returns true if loaded plugin successfully
        url = f"{self.base_url}/tts"
        query_params = {"text": text}

        try:
            logger.info(f'[PMHelper/tts] Sending a post request to voicevox, generating audio data for {text}')
            response = await self.client.post(url, params=query_params)
            if response.status_code == 200:
                logger.info(f'[PMHelper/tts] Generated audio successfully')
                return response.content

            reason = response.json()['detail']
            logger.error(f"[PMHelper/tts] Failed to generate audio data, reason: {reason}")
            return False
        except Exception as e:
            logger.error(f"[PMHelper/tts] Exception: {e}")
            return False

    async def transcribe(self, audio_data: bytearray) -> str:  # this is wrong
        # returns true if loaded plugin successfully
        url = f"{self.base_url}/transcribe"
        files = {"file": audio_data}

        try:
            logger.info(f'[PMHelper/transcribe] Sending a post request to whisper, transcribe data')
            response = await self.client.post(url, files=files)
            if response.status_code == 200:
                logger.info(f'[PMHelper/transcribe] Transcribed data successfully')
                return response.json()['transcription']

            reason = response.json()['detail']  # ?
            logger.error(f"[PMHelper/transcribe] Failed to transcribe data, reason: {reason}")
            return False
        except Exception as e:
            logger.error(f"[PMHelper/transcribe] Exception: {e}")
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        # returns true if unloaded plugin successfully
        url = f"{self.base_url}/unload_plugin"
        query_params = {"plugin_name": plugin_name}

        try:
            logger.info(f'[PMHelper/unload_plugin] Sending a post request to unload {plugin_name} plugin')

            response = await self.client.post(url, params=query_params)
            if response.status_code == 200:
                logger.info(f'[PMHelper/unload_plugin] Plugin {plugin_name} was unloaded successfully')
                return True

            reason = response.json()['detail']
            logger.error(f"[PMHelper/unload_plugin] Failed unload plugin {plugin_name}, reason: {reason}")
            return False
        except Exception as e:
            logger.error(f"[PMHelper/unload_plugin] Exception: {e}")
            return False

    async def load_plugin(self, plugin_name: str) -> bool:
        # returns true if loaded plugin successfully
        url = f"{self.base_url}/load_plugin"
        query_params = {"plugin_name": plugin_name}

        try:
            logger.info(f'[PMHelper/load_plugin] Sending a post request to load {plugin_name} plugin')

            response = await self.client.post(url, params=query_params)
            if response.status_code == 200:
                logger.info(f'[PMHelper/load_plugin] Plugin {plugin_name} was loaded successfully')
                return True

            reason = response.json()['detail']
            logger.error(f"[PMHelper/load_plugin] Failed load plugin {plugin_name}, reason: {reason}")
            return False
        except Exception as e:
            logger.error(f"[PMHelper/load_plugin] Exception: {e}")
            return False

    async def is_alive(self) -> bool:
        url = f"{self.base_url}/is_alive"

        try:
            logger.info(f'[PMHelper/is_alive] Sending a get request to see if the server is alive')
            response = await self.client.get(url)
            if response.status_code == 200:
                logger.info(f'[PMHelper/is_alive] Server is alive')
                return True

            reason = response.json()['detail']
            logger.error(f"[PMHelper/is_alive] Failed to connect to the server. reason: {reason}")
            return False
        except Exception as e:
            logger.error(f"[PMHelper/is_alive] Exception: {e}")
            return False

    async def is_plugin_loaded(self, plugin_name: str) -> bool:
        url = f"{self.base_url}/is_plugin_loaded"
        query_params = {"plugin_name": plugin_name}

        try:
            logger.info(f'[PMHelper/is_alive] Sending a get request to see if a plugin {plugin_name} is loaded')
            response = await self.client.get(url, params=query_params)
            if response.status_code == 200:
                logger.info(f'[PMHelper/is_plugin_loaded] Plugin {plugin_name} is loaded')
                return True

            reason = response.json()['detail']
            logger.error(f"[PMHelper/is_plugin_loaded] Plugin {plugin_name} is not loaded, reason: {reason}")
            return False
        except Exception as e:
            logger.error(f"[PMHelper/is_plugin_loaded] Exception: {e}")
            return False

    async def _shutdown_server(self) -> bool:
        url = f"{self.base_url}/shutdown"

        try:
            logger.info(f"[PMHelper/_shutdown_server] Sending post request to shutdown plugin manager server")
            response = await self.client.post(url)
            if response.status_code == 200:
                logger.info(
                    f"[PMHelper/_shutdown_server] Successfully shutdown plugin manager server")
                return True

            reason = response.json()['detail']
            logger.error(f"[PMHelper/_shutdown_server] Failed to shutdown server {response.status_code}: {reason}")
            return False
        except Exception as e:
            logger.error(f"[PMHelper/_shutdown_server] Exception: {e}")
            return False

    async def close(self):
        logger.info(f"[PMHelper/close] Trying to close fastapi server")
        did_shutdown = await self._shutdown_server()
        if not did_shutdown:
            logger.error(f"[PMHelper/close] Couldn't close fastapi server")
            return
        logger.info(f"[PMHelper/close] Closed fastapi server")
        logger.info(f"[PMHelper/close] Closing async client")
        await self.client.aclose()
        return did_shutdown
