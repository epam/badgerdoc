import logging
from airflow.decorators import task
from pprint import pformat

logger = logging.getLogger(__name__)


@task
def print_context(**context) -> dict:
    logger.info('PARAMS: ' + pformat(context))
    return context.get('params', {}) or {'empty': True}
