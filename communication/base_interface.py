import asyncio
import threading
from abc import ABC, abstractmethod
import logging
logger = logging.getLogger("bot")

class BaseInterface(ABC):
    @abstractmethod
    def tts(self, message: str):
        pass

    @abstractmethod
    def stt(self, intput: bytes):
        pass

    @abstractmethod
    def llm_interfere(self, message: str):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def initialize(self):
        pass

    def start_in_thread(self):
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()


