from pathlib import Path
import os
import sys
from abc import ABC, abstractmethod

import yaml
from dotenv import load_dotenv
from logging.config import dictConfig
import logging
from dataclasses import dataclass, asdict

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')

BASE_DIR = Path(os.getcwd())
Profiles_dir = BASE_DIR / "profiles" / "settings.yaml"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {
            "format": "%(levelname)-10s - %(name)-15s : %(message)s"
        }
    },
    "handlers": {
        "console": {
            'level': "DEBUG",
            'class': "logging.StreamHandler",
            'formatter': "verbose",
            'stream': sys.stdout
        },
        "console2": {
            'level': "WARNING",
            'class': "logging.StreamHandler",
            'formatter': "standard"
        },
        # "file": {
        #     'level': "INFO",
        #     'class': "logging.FileHandler",
        #     'filename': "logs/infos.log",
        #     'mode': "w",
        #     'formatter': "verbose"
        # },
    },
    "loggers": {
        "bot": {
            'handlers': ['console'],
            "level": "DEBUG",
            "propagate": False
        },
        # "telegram": {
        #     'handlers': ['console2', "file"],
        #     "level": "INFO",
        #     "propagate": False
        # }
    }
}

dictConfig(LOGGING_CONFIG)


@dataclass
class BaseSettings(ABC):
    @abstractmethod
    def validate(self):
        pass

    def load_from_yaml(self, filepath: str):
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                for key, value in data.items():
                    setattr(self, key, value)

    def save_to_yaml(self, filepath: str):
        with open(filepath, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)

    def __repr__(self):
        return yaml.dump(asdict(self), default_flow_style=False)


@dataclass
class TelegramSettings(BaseSettings):
    def validate(self):
        pass

    bot_username: str
    bot_nickname: str  # used for storing in the vectordb
    creator_id: id | None  # whitelist
    creator_username: str  # used for storing in the vectordb
    sticker_path: str | None


@dataclass
class WeaviateSettngs:
    class_name: str = "MemoryK"  # for testing i will use an already created class
    port: int = 8080
    host: str = "localhost"
    scheme: str = "http"

    @property
    def client_url(self):
        return f"{self.scheme}://{self.host}:{self.port}"


@dataclass
class PluginsSettings:
    llm_host: str


def get_logger(name="bot"):
    return logging.getLogger(name)
