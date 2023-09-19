"""Example DAG demonstrating the usage of the BashOperator."""
from __future__ import annotations

import datetime
from pprint import pprint

import pendulum
from airflow import DAG
from airflow.decorators import task, dag
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

with DAG(
    dag_id="print_params_operator",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=["badgerdoc"],
    params={"files_data": []},
) as dag:  # noqa
    @task
    def print_context(**context):
        pprint(context['params'])

    print_context()


if __name__ == "__main__":
    dag.test()
