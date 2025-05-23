import dataclasses
import os
from typing import Any, Dict, Iterator, List

import airflow_client.client as client
from airflow_client.client.api.dag_api import DAGApi
from airflow_client.client.api.dag_run_api import DAGRunApi
from airflow_client.client.model.dag import DAG
from airflow_client.client.model.dag_run import DAGRun
from airflow_client.client.rest import ApiException

import jobs.pipeline as pipeline
from jobs.schemas import AirflowPipelineStatus

AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD")
AIRFLOW_SERVICE_PORT = os.getenv("AIRFLOW_SERVICE_PORT")

AIRFLOW_URL = (
    f"{os.getenv('AIRFLOW_SERVICE_SCHEME')}://"
    f"{os.getenv('AIRFLOW_SERVICE_HOST')}"
)
if AIRFLOW_SERVICE_PORT:
    AIRFLOW_URL = f"{AIRFLOW_URL}:{AIRFLOW_SERVICE_PORT}"

AIRFLOW_URL = f"{AIRFLOW_URL}{os.getenv('AIRFLOW_SERVICE_PATH_PREFIX')}"


def get_configuration():
    return client.Configuration(
        username=AIRFLOW_USERNAME,
        password=AIRFLOW_PASSWORD,
        host=AIRFLOW_URL,
    )


def get_api_instance():
    configuration = get_configuration()
    with client.ApiClient(configuration) as api_client:
        yield api_client


async def get_dags() -> List[pipeline.AnyPipeline]:
    configuration = get_configuration()
    with client.ApiClient(configuration) as api_client:
        dag_api = DAGApi(api_client)
        # todo: map result to pipeline.AnyPipeline
        return dag_api.get_dags()


async def activate_dag(dag_id: str, api_client: client.ApiClient) -> None:
    try:
        api_instance = DAGApi(api_client)

        dag = api_instance.get_dag(dag_id)
        if dag.is_paused:
            updated_dag = DAG(is_paused=False)
            api_instance.patch_dag(dag_id, updated_dag)
    except ApiException as err:
        raise RuntimeError(
            f"Failed to fetch or update DAG state. DAG id: {dag_id}"
        ) from err
    except AttributeError as err:
        raise RuntimeError(
            f"Error while passing attributes. DAG id: {dag_id}"
        ) from err


async def fetch_dag_status(
    dag_id: str,
    dag_run_id: str,
    api_client: client.ApiClient,
) -> AirflowPipelineStatus:
    try:
        api_instance = DAGRunApi(api_client)
        api_response = api_instance.get_dag_run(dag_id, dag_run_id)
        dag_state = api_response.state.value
    except ApiException as err:
        raise RuntimeError(
            f"Error fetching DAG run status. Job id: {dag_id}"
        ) from err
    except (ValueError, TypeError, AttributeError) as err:
        raise RuntimeError(
            f"Error ApiClient incorrectly configured. DAG id: {dag_id}"
        ) from err

    if dag_state in (
        AirflowPipelineStatus.success.value,
        AirflowPipelineStatus.failed.value,
        AirflowPipelineStatus.running.value,
    ):
        return dag_state

    raise RuntimeError(f"Unexpected DAG run state: {dag_state}")


# todo: should we remove this?
def files_data_to_pipeline(
    files_data: List[Dict[str, Any]],
    job_id: int,
) -> Iterator[pipeline.PipelineFile]:
    for file in files_data:
        yield pipeline.PipelineFile(
            bucket=file["bucket"],
            input=pipeline.PipelineFileInput(job_id=job_id),
            input_path=file["file"],
            pages=file["pages"],
        )


async def run(
    pipeline_id: str,
    job_id: int,
    files: List[pipeline.PipelineFile],
    current_tenant: str,
    datasets: List[pipeline.Dataset],
    revisions: List[str],
) -> None:
    configuration = get_configuration()
    with client.ApiClient(configuration) as api_client:
        dag_run_api = DAGRunApi(api_client)
        dag_run_id = f"{pipeline_id}:{job_id}"
        dag_run = DAGRun(
            dag_run_id=dag_run_id,
            conf=dataclasses.asdict(
                pipeline.PipelineRunArgs(
                    job_id=job_id,
                    tenant=current_tenant,
                    files_data=files,
                    datasets=datasets,
                    revisions=revisions,
                )
            ),
        )
        dag_run_api.post_dag_run(pipeline_id, dag_run, async_req=True).get()


class AirflowPipeline(pipeline.BasePipeline):
    async def list(self) -> List[pipeline.AnyPipeline]:
        # todo: bind to AnyPipeline
        return await get_dags()

    async def run(
        self,
        pipeline_id: str,
        job_id: str,
        files: List[pipeline.PipelineFile],
        current_tenant: str,
        datasets: List[pipeline.Dataset],
        revisions: List[str],
    ) -> None:
        return await run(
            pipeline_id, job_id, files, current_tenant, datasets, revisions
        )
