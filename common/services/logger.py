import logging
import os
import sys
from pathlib import Path

LOGGING_FORMAT = logging.Formatter(
    fmt="[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
)


def get_logger(name: str, log_env: str, log_file: str) -> logging.Logger:
    """
    Setup logger object.
    """
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(LOGGING_FORMAT)

    env_log_name = os.environ.get(log_env)
    if env_log_name:
        log_filename = Path(env_log_name)
    else:
        log_filename = Path(__file__).parents[1] / f"{log_file}.log"
        logging.warning(
            "A log file doesn't define. The standard path is %s", log_filename
        )
    log_filename.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(LOGGING_FORMAT)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    return logger
