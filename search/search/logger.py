import logging
import sys

FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    " - %(filename)s - %(lineno)s - %(funcName)s"
)
DATE_FORMAT = "%d-%m-%Y %H:%M:%S"
LOGGING_FORMAT = logging.Formatter(
    fmt=FORMAT,
    datefmt=DATE_FORMAT,
)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(LOGGING_FORMAT)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    return logger


logger = get_logger("search")
