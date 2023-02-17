import logging
import traceback
from logging.config import dictConfig

from processing.config import settings

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "[%(asctime)s] - [%(name)s] - " "[%(levelname)s] - %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": settings.log_file,
        },
    },
    "loggers": {
        "": {"handlers": ["default", "file"], "level": "WARNING"},
    },
}

dictConfig(log_config)


def get_logger(name: str, level: int = settings.log_level) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def get_log_exception_msg(err: Exception) -> str:
    return (
        "=" * 20
        + "\n"
        + str(
            {
                "error_name": err.__class__.__name__,
                "error_msg": str(err),
                "traceback": "".join(
                    traceback.format_exception(None, err, err.__traceback__)
                ),
            }
        )
    )
