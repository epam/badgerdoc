# TODO: create unified logging for all microservices
import logging
import os

_log_format = (
    "%(asctime)s - [%(levelname)s] - %(name)s - "
    "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)
_datefmt = "%d-%b-%y %H:%M:%S"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


logging.basicConfig(level=LOG_LEVEL, format=_log_format, datefmt=_datefmt)
Logger = logging.getLogger(__name__)
