import io
from dataclasses import dataclass
from fastapi import APIRouter, UploadFile, File
from httpx import AsyncClient, ReadTimeout  # HTTP requests


@dataclass
class WhisperConfig:
    name: str
    entry_point: str
    class_name: str
    config_class_name: str
    host: str
    port: id
    save_to_file: bool


class Whisper:
    def __init__(self, logger, config):
        super().__init__()
        self.logger = logger
        self.config = config
        self.client = AsyncClient()
        self.base_url = f"http://{self.config.host}:{self.config.port}"
        self.router = APIRouter()

        @self.router.post("/transcribe")
        async def transcribe_file(file: UploadFile = File(...)):
            self.logger.debug(f"[Whisper/post.transcribe_file] Received file: {file.filename}")
            audio_data = await file.read()
            transcription = await self._transcribe_from_bytes(io.BytesIO(audio_data))
            return {"transcription": transcription}

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
        query_params = {"output": "txt", "language": "ja"}
        files = {'audio_file': b_data}
        try:
            self.logger.info(f'[Whisper/_transcribe_from_bytes] Sending a post request for audio transcription.')
            response = await self.client.post(url, files=files, params=query_params)
            response.raise_for_status()
            self.logger.info(f'[Whisper/_transcribe_from_bytes] Audio transcription was generated successfully')
            return response.text
        except ReadTimeout as e:  # this shit is too random :notlikethis:
            self.logger.error(f"[Whisper/_transcribe_from_bytes] Exception: {e}, failed on post.")
            return False
        except Exception as e:
            self.logger.error(
                f"[Whisper/_transcribe_from_bytes] Exception: {e}, response: {response}")  # I hope response wont error here :kashiwade:
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

    def get_route(self):
        """Returns the router for plugin manager to mount"""
        return self.router
