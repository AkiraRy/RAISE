from dataclasses import dataclass, field
from telegram.ext import CallbackContext
from typing import Optional

from telegram import Update


@dataclass
class TextMessage:
    content: str


@dataclass
class PhotoMessage:
    image: bytes  # i assume we will store image as bytes, might change in future


@dataclass
class VoiceMessage:
    voice: bytes  # i assume we will store voice as bytes, might change in future


@dataclass
class Message:
    id: int
    text_message: Optional[TextMessage] = field(default=None)
    photo_message: Optional[PhotoMessage] = field(default=None)
    voice_message: Optional[VoiceMessage] = field(default=None)

    response_message: Optional[str] = None


@dataclass
class TelegramMessage(Message):
    update: Update = field(default=None)
    context: CallbackContext = field(default=None)
