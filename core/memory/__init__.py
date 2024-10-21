from abc import ABC, abstractmethod


class Async_DB_Interface(ABC):
    @abstractmethod
    async def connect_db(self):
        pass

    @abstractmethod
    async def add_data(self, *args, **kwargs):
        pass

    @abstractmethod
    async def retrieve(self, *args, **kwargs):
        pass

    @abstractmethod
    async def close(self):
        pass
