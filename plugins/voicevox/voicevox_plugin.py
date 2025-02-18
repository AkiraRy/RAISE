import io
import os

from .. import Base
from httpx import AsyncClient  # HTTP requests
from dataclasses import dataclass

from config import AUDIO_DIR # temp?

# create config class for voicevox
# probably xml/json is better?
# i should also give path from root

request_access = ["AUDIO_DIR", "AUDIO_FILE_NAME", ]  # not implemented

@dataclass
class VVConfig:
    # make it save in this path?
    speaker_id: int
    host: str
    port: id
    save_to_file: bool


def save_to_file(path, data):
    with open(f"{path}\\temp.mp3", "wb") as f:  # name of the file add to config
        f.write(data)


class Voicevox(Base):
    def __init__(self, logger, config: VVConfig):
        super().__init__()
        self.logger = logger
        self.config = config
        self.client = AsyncClient()
        self.base_url = f"http://{self.config.host}:{self.config.port}"

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
            self.logger.error("temp, no voicebytes")
            # log?
            return False

        if self.config.save_to_file:
            save_to_file(AUDIO_DIR, voice_bytes)

        return voice_bytes # add more logging

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
            # log?
            self.logger.error("temp, no audioquery")
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
