import atexit
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
from logging.config import dictConfig
import logging
atexit.register(logging.shutdown)

# TODO AT THE TOP OF THIS FILE ADD CHECKER FOR EVERY PATH< BUT BETTER DO IT IN THE INNIT
load_dotenv()

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / 'logs'
LOGS_FILE = LOGS_DIR / 'infos.log'
WEAVIATE_LOG_FILE = LOGS_DIR / 'weaviate.log'
BRAIN_LOG_FILE = LOGS_DIR / 'brain.log'
PLUGIN_MANAGER_LOG_FILE = LOGS_DIR / "pm.log"

# Settings
CONFIG_DIR = BASE_DIR / 'config'
PROFILES_DIR = CONFIG_DIR / "profiles"
LLM_SETTINGS_DIR = CONFIG_DIR / "llm_settings"
DEFAULT_SETTINGS_FILE = "default_settings.yaml"
DEFAULT_SETTINGS = PROFILES_DIR / DEFAULT_SETTINGS_FILE

config_name = f'{os.getenv("config_name", "").strip()}.yaml'
SETTINGS_FROM_ENV = PROFILES_DIR / config_name

# Assets
ASSETS_DIR = BASE_DIR / "assets"
BACKUP_DIR = ASSETS_DIR / "db_backups"
MODEL_DIR = ASSETS_DIR / 'models'
PERSONA_DIR = ASSETS_DIR / 'persona_description'
PROMPT_TEMPLATES_DIR = ASSETS_DIR / "prompt_templates"

# Discord Related
COGS_DIR = BASE_DIR / 'communication' / 'discord' / "cogs"

# Plugin Related (temp?)
AUDIO_DIR = ASSETS_DIR / "audio"
PLUGIN_BASE_DIR = BASE_DIR / "plugins"
VOICEVOX_FILE_NAME = "vv_temp.mp3"
COMMUNICATION_FILE_NAME = "c_temp.mp3"  # used for temp audio files, that we get from communication module for whisper transcription

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
        "file": {  # not used anywhere?
            'level': "INFO",
            'class': "logging.FileHandler",
            'filename': f"{LOGS_FILE}",
            'mode': "w",
            'formatter': "verbose"
        },
        "weaviate_file": {
            'level': "DEBUG",
            'class': "logging.FileHandler",
            'filename': f"{WEAVIATE_LOG_FILE}",
            'mode': "a",
            'formatter': "verbose"
        },
        "brain_file": {
            'level': "DEBUG",
            'class': "logging.FileHandler",
            'filename': f"{BRAIN_LOG_FILE}",
            'mode': "a",
            'formatter': "verbose"
        },
        "pm_file": {
            'level': "DEBUG",
            'class': "logging.FileHandler",
            'filename': f"{PLUGIN_MANAGER_LOG_FILE}",
            'mode': "a",
            'formatter': "verbose"
        }
    },
    "loggers": {
        "programming": {
            'handlers': ['console'],
            "level": "DEBUG",
            "propagate": False
        },
        "weaviate_logger": {  # New logger for the weaviate logs
            'handlers': ['weaviate_file'],
            "level": "INFO",
            "propagate": False
        },
        "brain_logger": {  # New logger for the weaviate logs
            'handlers': ['brain_file'],
            "level": "INFO",
            "propagate": False
        },
        "pm_logger": {  # New logger for the weaviate logs
            'handlers': ['pm_file'],
            "level": "INFO",
            "propagate": False
        }
    }
}

dictConfig(LOGGING_CONFIG)


def get_logger(name="programming"):
    return logging.getLogger(name)


def ensure_directory_exists(path: Path):
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {path}")
        except OSError as e:
            logger.error(f"Error creating directory {path}: {e}")
            raise


ensure_directory_exists(CONFIG_DIR)
ensure_directory_exists(PROFILES_DIR)
ensure_directory_exists(LLM_SETTINGS_DIR)
ensure_directory_exists(ASSETS_DIR)
ensure_directory_exists(BACKUP_DIR)
ensure_directory_exists(MODEL_DIR)
ensure_directory_exists(PROMPT_TEMPLATES_DIR)
ensure_directory_exists(PERSONA_DIR)
ensure_directory_exists(LOGS_DIR)

logger = get_logger()
