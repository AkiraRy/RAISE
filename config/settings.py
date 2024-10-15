from pathlib import Path
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Type, Optional

import yaml
from dotenv import load_dotenv
from logging.config import dictConfig
import logging
from dataclasses import dataclass, asdict, field

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')

BASE_DIR = Path(os.getcwd())
PROFILES_DIR = BASE_DIR / "profiles"
DEFAULT_SETTINGS = PROFILES_DIR / "settings.yaml"

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
            yaml.dump(asdict(self), f)

    def __repr__(self):
        return yaml.dump(asdict(self))


@dataclass
class TelegramSettings(BaseSettings):
    def validate(self):
        errors = []
        if not self.bot_username:
            errors.append("Bot username is required.")
        if self.creator_id <= 0:
            errors.append("Creator ID must be a positive integer.")
        if errors:
            raise ValueError(f"Validation errors in TelegramSettings: {', '.join(errors)}")

    bot_username: str = ""
    bot_nickname: str = ""  # used for storing in the vectordb
    creator_id: int = -1  # whitelist
    creator_username: str = ""  # used for storing in the vectordb
    sticker_path: str = ""


@dataclass
class WeaviateSettings(BaseSettings):
    def validate(self):
        errors = []
        if not self.class_name:
            errors.append("Class name is required.")
        if not (0 < self.port < 65536):
            errors.append("Port must be a valid number between 1 and 65535.")
        if errors:
            raise ValueError(f"Validation errors in WeaviateSettings: {', '.join(errors)}")

    class_name: str = "MemoryK"  # for testing i will use an already created class
    port: int = 8080
    host: str = "localhost"
    scheme: str = "http"

    @property
    def client_url(self):
        return f"{self.scheme}://{self.host}:{self.port}"


@dataclass
class PluginSettings:
    plugin_name: str
    plugin_config: Dict[str, str] = field(default_factory=dict)


@dataclass
class DiscordSettings(BaseSettings):
    def validate(self):
        pass

    bot_name: str = ""


@dataclass
class Config(BaseSettings):
    telegram: Optional[TelegramSettings] = None
    discord: Optional[DiscordSettings] = None
    weaviate: Optional[WeaviateSettings] = None
    plugins: Dict[str, PluginSettings] = field(default_factory=dict)

    def validate(self):
        if not self.weaviate:
            raise ValueError("Weaviate must exists")
        if not (self.telegram or self.discord):
            raise ValueError("At least one of Telegram, Discord, or Weaviate settings must be provided.")

        if self.telegram:
            self.telegram.validate()
        if self.discord:
            self.discord.validate()
        if self.weaviate:
            self.weaviate.validate()


class SettingsManager:
    def __init__(self, config: Config = Config(),  yaml_path: Path = DEFAULT_SETTINGS):
        self.config: Config = config
        self.yaml_path = Path(yaml_path)  # Path to the single YAML file

    def load_settings(self):
        if self.yaml_path.exists():
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f)

            if 'telegram' in data:
                self.config.telegram = TelegramSettings(**data['telegram'])
            if 'discord' in data:
                self.config.discord = DiscordSettings(**data['discord'])
            if 'weaviate' in data:
                self.config.weaviate = WeaviateSettings(**data['weaviate'])
            if 'plugins' in data:
                for name, settings in data['plugins'].items():
                    self.config.plugins[name] = PluginSettings(plugin_name=name, plugin_config=settings)

            self.config.validate()
            print("Settings loaded successfully.")

    def save_settings(self):
        all_settings = {}
        if self.config.telegram:
            all_settings['telegram'] = asdict(self.config.telegram)
        if self.config.discord:
            all_settings['discord'] = asdict(self.config.discord)
        if self.config.weaviate:
            all_settings['weaviate'] = asdict(self.config.weaviate)

        all_settings['plugins'] = {name: asdict(plugin) for name, plugin in self.config.plugins.items()}

        with open(self.yaml_path, 'w') as f:
            yaml.dump(all_settings, f, default_flow_style=False)
            print("Settings saved successfully.")


def get_logger(name="bot"):
    return logging.getLogger(name)
