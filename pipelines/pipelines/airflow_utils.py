from collections import OrderedDict
from datetime import datetime
from typing import List

import airflow_client.client as client
from airflow_client.client.model.dag import DAG

import pipelines.config as config
from pipelines.schemas import InputArguments, PipelineOut


def get_configuration():
    return client.Configuration(
        username=config.AIRFLOW_USERNAME,
        password=config.AIRFLOW_PASSWORD,
        host=config.AIRFLOW_URL,
    )


def get_api_instance():
    configuration = get_configuration()

    with client.ApiClient(configuration) as api_client:
        yield api_client


def dag2pipeline(dag: DAG):
    return PipelineOut(
        type="airflow",
        is_latest=False,
        version=1,
        date=datetime.today(),
        meta=dag.to_dict(),
        steps=[],
        name=f"{dag['dag_id']}:airflow",
        id=0,
    )


def input_data_to_dag_args(data: List[InputArguments], job_id: int, tenant):
    dag_args = OrderedDict()

    for file in data:
        if file.file in dag_args:
            dag_args[file.file].setdefault("pages", []).extend(file.pages)
            continue

        dag_args[file.file] = file.to_dict_for_airflow(job_id, tenant)

    return list(dag_args.values())
