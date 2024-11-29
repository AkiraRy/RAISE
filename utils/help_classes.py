from dataclasses import dataclass, field
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


@dataclass
class TelegramMessage(Message):
    update: Update = field(default=None)
    context: CallbackContext = field(default=None)


@dataclass
class DiscordMessage(Message):
    channel: Msg.channel = field(default=None)
