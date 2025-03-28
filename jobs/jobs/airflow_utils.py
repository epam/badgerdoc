import asyncio
import dataclasses
import os
import time
from typing import Any, Dict, Iterator, List

import airflow_client.client as client
from airflow_client.client.api.dag_api import DAGApi
from airflow_client.client.api.dag_run_api import DAGRunApi
from airflow_client.client.model.dag_run import DAGRun
from airflow_client.client.api import task_instance_api
from airflow_client.client.rest import ApiException
from airflow_client.client.model.dag import DAG

import jobs.pipeline as pipeline

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


async def get_dag_status(dag_id: str, job_id: int): 
    """Fetches the latest DAG run status for the given DAG ID."""
    
    configuration = get_configuration()

    try:
        with client.ApiClient(configuration) as api_client:
        
            dag_run_id = f"{dag_id}:{job_id}"
            api_instance = DAGRunApi(api_client) 
            
            # activate dag if it is paused
            await activate_dag(dag_id)           
            
            api_response = api_instance.get_dag_run(dag_id, dag_run_id)
            dag_status = 1 if api_response.state.value == "success" else 0

            return {"finished": dag_status, "total": 1}

    except ApiException as e:
        return f"error fetching DAG run status: {str(e)}"
    except Exception as e:
        return f"errorUnexpected error: {str(e)}"
    
    
async def activate_dag(dag_id: str):
    
    configuration = get_configuration()  
    
    try:
        with client.ApiClient(configuration) as api_client:
            api_instance = DAGApi(api_client)

            dag = api_instance.get_dag(dag_id)
            
            if dag.is_paused:
                updated_dag = DAG(is_paused=False)
                api_instance.patch_dag(dag_id, updated_dag)
                
    except ApiException as e:
        return f"error fetching DAG state: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
    
async def wait_for_dag_completion_async(dag_id: str, dag_run_id: str, poll_interval=2, timeout=600):
    """waiting for DAG completion."""

    configuration = get_configuration()
    
    try:
        with client.ApiClient(configuration) as api_client:
            api_instance = DAGRunApi(api_client)

            start_time = time.time()
            while time.time() - start_time < timeout:
                api_response = api_instance.get_dag_run(dag_id, dag_run_id)
                dag_state = api_response.state.value

                if dag_state in ["success", "failed"]:
                    return dag_state

                await asyncio.sleep(poll_interval)

    except ApiException as e:
        return f"error fetching DAG state: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
    return "Timeout reached"


            
# This function is not used but can be used in the future instead of get_dag_status for better progress bar display. 
async def get_dag_task_summary(dag_id: str, job_id: int):
    """Finds the total number of tasks in a DAG run and counts how many have succeeded."""
    
    configuration = get_configuration()

    with client.ApiClient(configuration) as api_client:
        try:
            api_instance = task_instance_api.TaskInstanceApi(api_client)

            dag_run_id = f"{dag_id}:{job_id}"
            api_response = api_instance.get_task_instances(dag_id=dag_id, dag_run_id=dag_run_id)

            task_instances = api_response.task_instances

            total_tasks = len(task_instances)
            if total_tasks == 0:
                raise ValueError(f"No tasks found for DAG ID: {dag_id}, JOB ID: {job_id}")

            successful_tasks = sum(1 for task in task_instances if task.state.value == "success")

            return f"DAG ID: {dag_id}, DAG Run ID: {dag_run_id}, Total Tasks: {total_tasks}, Successful Tasks: {successful_tasks}"
        except ApiException as e:
            return f"Error fetching tasks for DAG ID: {dag_id}, DAG Run ID: {dag_run_id}. Details: {e}"
        except ValueError as e:
            return str(e)  
        except Exception as e:
            return f"Unexpected error occurred: {str(e)}"    





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
