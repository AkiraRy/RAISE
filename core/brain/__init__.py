from typing import Optional, Literal
from dataclasses import dataclass
from config import (PROFILES_DIR,
                    logger,
                    LLMSettings,
                    MODEL_DIR,
                    SettingsManager,
                    LLM_SETTINGS_DIR,
                    PROMPT_TEMPLATES_DIR)


@dataclass
class PromptMessage:
    role: Literal['system', 'user']
    content: str


@dataclass
class ResponseContent:
    content: str
    finish_reason: Optional[str]


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
