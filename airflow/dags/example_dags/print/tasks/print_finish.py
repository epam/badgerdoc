import logging
from airflow.decorators import task

logger = logging.getLogger(__name__)


@task
def print_finish(data: str):
    logger.info(data.upper())
