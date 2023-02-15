import logging
from typing import Any, Dict, Optional

from pipelines.config import LOG_LEVEL

_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
_datefmt = "%d-%b-%y %H:%M:%S"


def _get_stream_handler() -> logging.StreamHandler:  # type: ignore
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LOG_LEVEL)
    stream_handler.setFormatter(logging.Formatter(_log_format, _datefmt))
    return stream_handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(_get_stream_handler())
    return logger


def cut_dict_strings(
    d: Optional[Dict[str, Any]], max_length: int = 20
) -> Optional[Dict[str, Any]]:
    """Reduces the length of string values of 'd' dictionary
    for logging purposes.

    Args:
        d: any dictionary
        max_length: max length to reduce the strings.

    Returns:
        dict with reduced strings.
    """
    if d is None:
        return None

    def cut_if_str(value: Any) -> Any:
        if isinstance(value, str):
            to_add = "..." if len(value) > max_length else ""
            return value[:max_length] + to_add
        return value

    return {key: cut_if_str(value) for key, value in d.items()}
