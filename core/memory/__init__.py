from abc import ABC, abstractmethod


class Async_DB_Interface(ABC):
    @abstractmethod
    async def connect_db(self):
        pass

    @abstractmethod
    async def add_memories(self, *args, **kwargs):
        pass

    @abstractmethod
    async def retrieve(self, *args, **kwargs):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def get_context(self, *args, **kwargs):
        """get context using similarity search on the db data"""
        pass

    @abstractmethod
    async def get_chat_memory(self):
        pass