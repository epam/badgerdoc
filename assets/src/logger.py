import logging

from src.config import settings

_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"  # noqa
_datefmt = "%d-%b-%y %H:%M:%S"


def _get_file_handler() -> logging.FileHandler:
    file_handler = logging.FileHandler(
        f"{settings.app_name}_{settings.app_version}.log"
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(_log_format, _datefmt))
    return file_handler


def _get_stream_handler() -> logging.StreamHandler:  # type: ignore
    # for `-> logging.StreamHandler` and mypy 0.931 rises:
    # Missing type parameters for generic type "StreamHandler"
    # for `-> logging.StreamHandler[TextIO]` rises:
    # TypeError: 'type' object is not subscriptable

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(_log_format, _datefmt))
    return stream_handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if settings.log_file:
        logger.addHandler(_get_file_handler())
    logger.addHandler(_get_stream_handler())
    return logger
