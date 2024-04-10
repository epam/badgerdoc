import logging
import os

_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"  # noqa
_datefmt = "%d-%b-%y %H:%M:%S"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def _get_stream_handler() -> logging.StreamHandler:  # type: ignore
    # for `-> logging.StreamHandler` and mypy 0.931 rises:
    # Missing type parameters for generic type "StreamHandler"
    # for `-> logging.StreamHandler[TextIO]` rises:
    # TypeError: 'type' object is not subscriptable

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LOG_LEVEL)
    stream_handler.setFormatter(logging.Formatter(_log_format, _datefmt))
    return stream_handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(_get_stream_handler())
    return logger
