import logging

from scheduler import config

_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
_datefmt = "%d-%b-%y %H:%M:%S"


def _get_file_handler() -> logging.FileHandler:
    file_handler = logging.FileHandler(config.LOG_FILEPATH)
    file_handler.setLevel(config.LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter(_log_format, _datefmt))
    return file_handler


def _get_stream_handler() -> logging.StreamHandler:  # type: ignore
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(config.LOG_LEVEL)
    stream_handler.setFormatter(logging.Formatter(_log_format, _datefmt))
    return stream_handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if config.LOG_FILEPATH:
        logger.addHandler(_get_file_handler())
    logger.addHandler(_get_stream_handler())
    return logger
