import logging
import os

from core.memory import Async_DB_Interface, Memory, MemoryChain
from config import PROFILES_DIR, get_logger
logger = get_logger()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Brain(metaclass=Singleton):
    def __init__(self, memory_manager: Async_DB_Interface, persona_path: str, token_limit=1000):
        # memory_manager - db instance, persona - name of the file where persona is stored
        self.token_limit = token_limit
        self.memory_manager: Async_DB_Interface = memory_manager
        self.persona_path: str = persona_path
        self.persona: str = persona_path
        self.load_persona()

    def load_persona(self) -> None:
        logger.info("[brain/load_persona] Trying to load AI persona")
        try:
            path = PROFILES_DIR / f"{self.persona}.txt"
            logger.info(f"[brain/load_persona] Trying to load AI Persona from file at {path}")

            with open(path, 'r') as f:
                lines = f.readlines()
            self.persona = ''.join(lines)

        except IOError:
            logger.error(f"[brain/load_persona] There was an error during handling the file {self.persona}")
        else:
            logger.info(f"[brain/load_persona] Successfully loaded AI persona")

