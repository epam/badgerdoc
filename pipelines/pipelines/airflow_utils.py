from datetime import datetime

import pipelines.config as config
import airflow_client.client as client
from airflow_client.client.api import dag_api
from airflow_client.client.model.dag_collection import DAGCollection
from airflow_client.client.model.error import Error
from airflow_client.client.model.dag import DAG
from pipelines.schemas import PipelineOut

def get_configuration():
    return client.Configuration(
        username=config.AIRFLOW_USERNAME,
        password=config.AIRFLOW_PASSWORD,
        host=config.AIRFLOW_URL
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
        id=0
    )
