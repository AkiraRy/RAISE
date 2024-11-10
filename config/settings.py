from pathlib import Path
import sys
from dotenv import load_dotenv
from logging.config import dictConfig
import logging

# TODO AT THE TOP OF THIS FILE ADD CHECKER FOR EVERY PATH< BUT BETTER DO IT IN THE INNIT
load_dotenv()

BASE_DIR = Path(__file__).parent.parent

CONFIG_DIR = BASE_DIR / 'config'
PROFILES_DIR = CONFIG_DIR / "profiles"
LLM_SETTINGS_DIR = CONFIG_DIR / "llm_settings"
DEFAULT_SETTINGS_DIR = PROFILES_DIR / "settings.yaml"

ASSETS_DIR = BASE_DIR / "assets"
BACKUP_DIR = ASSETS_DIR / "db_backups"
MODEL_DIR = ASSETS_DIR / 'models'

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


def get_logger(name="bot"):
    return logging.getLogger(name)


logger = get_logger()


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
ensure_directory_exists(DEFAULT_SETTINGS_DIR)
ensure_directory_exists(ASSETS_DIR)
ensure_directory_exists(BACKUP_DIR)
ensure_directory_exists(MODEL_DIR)
