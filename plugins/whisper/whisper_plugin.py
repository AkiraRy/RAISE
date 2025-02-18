import io
from dataclasses import dataclass
from .. import Base
from httpx import AsyncClient  # HTTP requests


@dataclass
class WhisperConfig:
    host: str
    port: id
    save_to_file: bool


class Whisper(Base):
    def __init__(self, logger, config):
        super().__init__()
        self.logger = logger
        self.config = config
        self.client = AsyncClient()
        self.base_url = f"http://{self.config.host}:{self.config.port}"

    async def transcribe(self, data):
        if isinstance(data, io.BytesIO):
            self.logger.info(f"[Whisper/transcribe] transcribing binary data")
            return await self._transcribe_from_bytes(data)
        elif isinstance(data, str):
            self.logger.info(f"[Whisper/transcribe] transcribing data from file")
            return await self._transcribe_from_path(data)
        else:
            raise NotImplemented()

    async def _transcribe_from_bytes(self, b_data):
        url = f"{self.base_url}/asr"
        query_params = {"output": "txt"}
        files = {'audio_file': b_data}
        try:
            self.logger.info(f'[Whisper/_transcribe_from_bytes] Sending a post request for audio transcription.')
            response = await self.client.post(url, files=files, params=query_params)
            response.raise_for_status()
            self.logger.info(f'[Whisper/_transcribe_from_bytes] Audio transcription was generated successfully')
            return response.text
        except Exception as e:
            self.logger.error(
                f"[Whisper/_transcribe_from_bytes] Exception: {e}, response: {response}")  # it wont we referenced before initialization
            return False

    async def _transcribe_from_path(self, path):
        self.logger.info(f'[Whisper/_transcribe_from_path] Transcribing an audio file from path.')
        with open(path, 'rb') as file: # change to async file read later on
            return await self._transcribe_from_bytes(file)

    async def close(self):
        self.logger.info(f"[Whisper/close] stopping whisper plugin")
        # logic
        await self.client.aclose()
        return True
