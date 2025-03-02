from dataclasses import dataclass, field

from pydantic import BaseModel
from telegram.ext import CallbackContext
from typing import Optional
from datetime import datetime
from telegram import Update
from discord.message import Message as Msg
import abc
from enum import Enum

@dataclass
class TextMessage:
    content: str


@dataclass
class PhotoMessage:
    image: bytes  # I assume we will store image as bytes, might change in future


@dataclass
class VoiceMessage:
    voice: bytes  # I assume we will store voice as bytes, might change in future


@dataclass
class Message:
    id: int
    from_user: str
    datetime: datetime

    text_content: Optional[TextMessage] = field(default=None)
    photo_content: Optional[PhotoMessage] = field(default=None)
    voice_content: Optional[VoiceMessage] = field(default=None)

    # Data back from our model
    response_message: Optional[str] = None


# use this later
class PhotoMessage_server(BaseModel):
    image: bytes  # Store image as bytes.


class VoiceMessage_server(BaseModel):
    voice: bytes  # Store voice as bytes.


class Message_server(BaseModel):
    id: int
    from_user: str
    datetime: datetime
    text_content: str

    def dict(self, **kwargs):
        # Convert datetime to ISO format
        data = super().dict(**kwargs)
        data["datetime"] = self.datetime.isoformat()
        return data


@dataclass
class TelegramMessage(Message):
    update: Update = field(default=None)
    context: CallbackContext = field(default=None)


@dataclass
class DiscordMessage(Message):
    channel: Msg.channel = field(default=None)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class PluginType(Enum):
    TTS = 0
    STT = 1
    STS = 2
    ELSE = 3


class BasePlugin(abc.ABC):
    def __init__(self, plugin_type: PluginType, required_perms: list):
        self.plugin_type = plugin_type
        self.required_perms: list = required_perms
        self.perms: dict = {}

    def get_router(self):
        pass

    def close(self):
        pass
