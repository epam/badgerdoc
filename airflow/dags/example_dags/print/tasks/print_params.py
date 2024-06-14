import logging
from airflow.decorators import task
from pprint import pformat

logger = logging.getLogger(__name__)


@task
def print_params(data: dict, **kwargs) -> str:
    logger.info('PARAMS: ' + pformat(data))
    logger.info('KWARGS: ' + pformat(kwargs))
    return "finish"
""