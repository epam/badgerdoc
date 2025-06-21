import logging
from pprint import pformat

from airflow.decorators import task

logger = logging.getLogger(__name__)


@task
def print_params(data: dict, **kwargs) -> str:
    logger.info("PARAMS: " + pformat(data))
    logger.info("KWARGS: " + pformat(kwargs))
    return "finish"


""
