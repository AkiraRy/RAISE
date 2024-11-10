from abc import ABC

from config import WeaviateSettings
from core.memory import Async_DB_Interface
from weaviate import WeaviateAsyncClient


class WeaviateBase(Async_DB_Interface, ABC):
    def __init__(self, settings: WeaviateSettings):
        self.config: WeaviateSettings = settings
        self.client: WeaviateAsyncClient | None = None

