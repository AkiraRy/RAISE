from typing import Optional, Literal
from dataclasses import dataclass
from config import PROFILES_DIR, logger, LLMSettings, MODEL_DIR


@dataclass
class PromptMessage:
    role: Literal['system', 'user']
    content: str


@dataclass
class ResponseContent:
    message: dict[str, str]
    content: str
    finish_reason: Optional[Literal["stop", "length"]]


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
