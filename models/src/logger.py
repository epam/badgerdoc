import logging

_log_format = (
    f"%(asctime)s - [%(levelname)s] - %(name)s - "
    f"(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)
_datefmt = "%d-%b-%y %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
