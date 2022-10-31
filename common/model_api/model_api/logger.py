import logging
import os
import sys
from pathlib import Path

FORMAT = "%(levelname)s:    %(filename)s    %(funcName)s    %(asctime)s - %(message)s"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S"
LOGGING_FORMAT = logging.Formatter(
    fmt=FORMAT,
    datefmt=DATE_FORMAT,
)


def get_logger(name: str) -> logging.Logger:
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(LOGGING_FORMAT)

    env_log_name = os.environ.get("PREPROCESSING_LOG_FILE_PATH")
    if env_log_name:
        log_filename = Path(env_log_name)
    else:
        log_filename = Path(__file__).parent / "molecule_recognizer.log"
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


logging.basicConfig(format=FORMAT, datefmt=DATE_FORMAT)
