import pathlib
import os
import sys

from dotenv import load_dotenv
from logging.config import dictConfig
import logging

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')

BASE_DIR = pathlib.Path(__file__).parent

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
