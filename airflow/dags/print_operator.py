"""Example DAG demonstrating the usage of the BashOperator."""
from __future__ import annotations

from datetime import datetime
from pprint import pprint

from airflow.decorators import task, dag
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection('minio')


@dag(schedule="@daily", start_date=datetime(2021, 12, 1), catchup=False, dag_id="print")
def taskflow():
    @task
    def print_context(**context) -> dict:
        # pprint(context)
        pprint([conn.__dict__])
        return context.get('params', {})

    @task
    def print_params(data: dict) -> str:
        pprint(data)
        return "finish"

    @task
    def print_finish(data: str):
        print(data)

    r1 = print_context()
    r2 = print_params(r1)
    print_finish(r2)


taskflow()
