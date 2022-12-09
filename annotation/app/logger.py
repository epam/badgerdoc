import logging

_log_format = (
    "%(asctime)s - [%(levelname)s] - %(name)s - "
    "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)
_datefmt = "%d-%b-%y %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=_log_format, datefmt=_datefmt)
Logger = logging.getLogger(__name__)
