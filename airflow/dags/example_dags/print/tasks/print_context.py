import logging
from pprint import pformat

from airflow.decorators import task

logger = logging.getLogger(__name__)


@task
def print_context(**context) -> dict:
    logger.info("PARAMS: " + pformat(context))
    return context.get("params", {}) or {"empty": True}
