from dataclasses import dataclass, field

from pydantic import BaseModel
from telegram.ext import CallbackContext
from typing import Optional
from datetime import datetime
from telegram import Update
from discord.message import Message as Msg


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


class PhotoMessage_server(BaseModel):
    image: bytes  # Store image as bytes.


class VoiceMessage_server(BaseModel):
    voice: bytes  # Store voice as bytes.


class Message_server(BaseModel):
    id: int
    from_user: str
    datetime: datetime
    text_content: Optional[str] = None
    photo_content: Optional[PhotoMessage] = None
    voice_content: Optional[VoiceMessage] = None

    def is_valid(self) -> bool:
        """Ensure at least one of text_content, photo_content, or voice_content is non-None."""
        return any([self.text_content, self.photo_content, self.voice_content])


@dataclass
class TelegramMessage(Message):
    update: Update = field(default=None)
    context: CallbackContext = field(default=None)


@dataclass
class DiscordMessage(Message):
    channel: Msg.channel = field(default=None)
