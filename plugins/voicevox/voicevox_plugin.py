import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from httpx import AsyncClient  # HTTP requests
from dataclasses import dataclass
from utils import BasePlugin

request_access = ["AUDIO_DIR", "VOICEVOX_FILE_NAME"]


@dataclass
class VVConfig:
    speaker_id: int
    host: str
    port: id
    save_to_file: bool
    name: str # do i need that?
    entry_point: str
    class_name: str
    config_class_name: str


def save_to_file(path, data):
    with open(path, "wb") as f:
        f.write(data)


class Voicevox(BasePlugin):
    def __init__(self, logger, config: VVConfig):
        super().__init__(request_access)
        self.logger = logger
        self.config = config
        self.client = AsyncClient()
        self.base_url = f"http://{self.config.host}:{self.config.port}"
        self.router = APIRouter()

        @self.router.post("/tts")
        async def generate_audio(text):
            self.logger.debug(f"[Voicevox/post.generate_audio] Received text: {text}")
            # preprocess text, before generating voice, or handle that before sending a request?
            voice_data = await self.generate_voice(text)
            if not voice_data:
                return HTTPException(status_code=500, detail="No audio data was generated")

            audio_buffer = io.BytesIO(voice_data)
            audio_buffer.seek(0)

            return StreamingResponse(audio_buffer, media_type="audio/wav")

    def get_router(self):
        """Returns the router for plugin manager to mount"""
        return self.router

    async def get_style_ids(self):
        url = f"{self.base_url}/speakers"
        try:
            self.logger.info(f'[Voicevox/get_style_ids] Sending a get request to get style ids')
            response = await self.client.get(url)
            response.raise_for_status()
            self.logger.info(f'[Voicevox/get_style_ids] Successfully got style ids')
            return response.json()
        except Exception as e:
            self.logger.error(f"[Voicevox/get_style_ids] Exception: {e}")
            return False

    async def generate_voice(self, text):
        # assume text is preprocessed before this function call
        audio_query_json = await self._generate_audio_query(text)
        voice_bytes = await self._generate_synthesis(audio_query_json)

        if not voice_bytes:
            self.logger.error("[Voicevox/generate_voice] No voice data was received.")
            return False

        audio_dir = self.perms.get(request_access[0])
        file_name = self.perms.get(request_access[1])

        if all([audio_dir, file_name, self.config.save_to_file]):
            self.logger.info("[Voicevox/generate_voice] Saving to temporary file.")
            save_to_file(f"{audio_dir}\\{file_name}", voice_bytes)

        return voice_bytes

    async def _generate_audio_query(self, text: str):
        url = f"{self.base_url}/audio_query"
        query_params = {"speaker": self.config.speaker_id, "text": text}

        try:
            self.logger.info(f'[Voicevox/_generate_audio_query] Sending a post request for audio query.')
            response = await self.client.post(url, params=query_params)
            response.raise_for_status()
            self.logger.info(f'[Voicevox/_generate_audio_query] Audio query was generated successfully')
            return response.json()

        except Exception as e:
            self.logger.error(
                f"[Voicevox/_generate_audio_query] Exception: {e}, response: {response}")  # it wont we referenced before initialization
            return False

    async def _generate_synthesis(self, audio_query) -> bytes | bool:
        if not audio_query:
            self.logger.error("[Voicevox/_generate_synthesis] No audio query data was receied")
            return False
        url = f"{self.base_url}/synthesis"
        query_params = {"speaker": self.config.speaker_id}
        headers = {"Content-Type": "application/json"}

        try:
            self.logger.info(f'[Voicevox/_generate_synthesis] Sending a post request for synthesis generation.')
            response = await self.client.post(
                url,
                params=query_params,
                json=audio_query,
                headers=headers
            )
            response.raise_for_status()
            self.logger.info(f'[Voicevox/_generate_synthesis] Synthesis was generated successfully')
            return response.content

        except Exception as e:
            self.logger.error(
                f"[Voicevox/_generate_synthesis] Exception: {e}, response: {response}")  # it wont we referenced before initialization
            return False

    async def close(self):
        self.logger.info(f"[Voicevox/close] stopping voicevox plugin")
        # logic
        await self.client.aclose()
        return True
