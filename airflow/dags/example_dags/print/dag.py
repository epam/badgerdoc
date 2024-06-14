"""Example DAG demonstrating the usage of the BashOperator."""
from __future__ import annotations

import logging 
from datetime import datetime

from airflow.decorators import dag

from example_dags.print.tasks import (
    print_context,
    print_params,
    print_finish,
)

logger = logging.getLogger(__name__)


@dag(schedule="@daily", start_date=datetime(2021, 12, 1), catchup=False, dag_id="print")
def taskflow():
    r1 = print_context()
    r2 = print_params(r1)
    print_finish(r2)


taskflow()
