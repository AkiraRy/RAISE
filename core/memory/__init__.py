from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, Field
from datetime import datetime


class Memory(BaseModel):
    from_name: str
    message: str
    time: datetime

    # metrics for similarity search
    distance: Optional[float] = None
    certainty: Optional[float] = None
    score: Optional[float] = None


class SimilaritySearch(BaseModel):
    memories: Optional[List[Memory]] = Field(default_factory=list)

    def add_object(self,
                   from_name: Optional[str] = None,
                   message: Optional[str] = None,
                   time: Optional[datetime] = None,
                   distance: Optional[float] = None,
                   certainty: Optional[float] = None,
                   score: Optional[float] = None,
                   *,
                   memory: Optional[Memory] = None):

        if memory:
            self.memories.append(memory)
        else:
            if from_name is None or message is None or time is None:
                raise ValueError("from_name, message, and time are required when memory is not provided")

            memory = Memory(
                from_name=from_name,
                message=message,
                time=time,
                distance=distance,
                certainty=certainty,
                score=score
            )
            self.memories.append(memory)


class Async_DB_Interface(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def add_memories(self, memory: Memory):
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
