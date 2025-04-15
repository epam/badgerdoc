from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple, Union

import aiohttp.client_exceptions
import airflow_client.client as client
import fastapi.encoders
from sqlalchemy.orm import Session

import jobs.airflow_utils as airflow_utils
import jobs.databricks_utils as databricks_utils
import jobs.pipeline as pipeline
from jobs import db_service
from jobs.config import (
    ANNOTATION_SERVICE_HOST,
    ASSETS_SERVICE_HOST,
    JOBS_SERVICE_HOST,
    JOBS_SIGNED_URL_ENABLED,
    JOBS_SIGNED_URL_KEY_NAME,
    PAGINATION_THRESHOLD,
    PIPELINES_SERVICE_HOST,
    ROOT_PATH,
    TAXONOMY_SERVICE_HOST,
    USERS_HOST,
)
from jobs.logger import logger
from jobs.models import CombinedJob
from jobs.s3 import create_pre_signed_s3_url
from jobs.schemas import (
    AirflowPipelineStatus,
    AnnotationJobUpdateParamsInAnnotation,
    CategoryLinkInput,
    CategoryLinkParams,
    JobType,
    JobParamsToChange,
    Status,
)


async def get_files_data_from_datasets(
    datasets_data: List[int], current_tenant: str, jw_token: str
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """Takes datasets tags from request_body.
    Returns list of dictionaries with data for an each file
    in datasets passed in request_body"""
    files_data: List[Dict[str, Any]] = []
    valid_dataset_tags: List[int] = []
    for dataset_id in datasets_data:
        try:
            logger.info(
                f"Sending request to the dataset manager "
                f"to get info about dataset {dataset_id}"
            )
            status, response = await fetch(
                method="GET",
                url=f"{ASSETS_SERVICE_HOST}/datasets/{dataset_id}/files",
                headers={
                    "X-Current-Tenant": current_tenant,
                    "Authorization": f"Bearer {jw_token}",
                },
                raise_for_status=True,
            )
            if status == 404:
                logger.error(
                    f"Failed request to the Dataset Manager: {response}"
                )
                continue
        except aiohttp.client_exceptions.ClientError as err:
            logger.exception(f"Failed request to the Dataset Manager: {err}")
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed request to the Dataset Manager: {err}",
            )

        valid_dataset_tags.append(dataset_id)
        files_data.extend(response)

    return files_data, valid_dataset_tags


async def get_files_data_from_separate_files(
    separate_files_ids: List[int], current_tenant: str, jw_token: str
) -> Union[Tuple[List[Any], List[int]]]:
    """Takes ids of files from request body.
    Returns list of dictionaries with data for an each file
    with ids passed in request_body"""
    splatted_separate_files_ids = list(split_list(separate_files_ids, 100))
    all_files_data = []
    for batch in splatted_separate_files_ids:
        elements_for_page_in_dataset_manager = 100
        try:
            params = {
                "pagination": {
                    "page_num": len(separate_files_ids)
                    // elements_for_page_in_dataset_manager
                    + 1,
                    "page_size": elements_for_page_in_dataset_manager,
                },
                "filters": [{"field": "id", "operator": "in", "value": batch}],
            }
            logger.info(
                "Sending request to the dataset manager "
                "to get info about files"
            )
            _, response = await fetch(
                method="POST",
                url=f"{ASSETS_SERVICE_HOST}/files/search",
                body=params,
                headers={
                    "X-Current-Tenant": current_tenant,
                    "Authorization": f"Bearer {jw_token}",
                },
                raise_for_status=True,
            )
        except aiohttp.client_exceptions.ClientError as err:
            logger.exception(f"Failed request to the Dataset Manager: {err}")
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed request to the Dataset Manager: {err}",
            )

        all_files_data.extend(response["data"])

    valid_separate_files_uuids = [
        file_data["id"] for file_data in all_files_data
    ]

    return all_files_data, valid_separate_files_uuids


def split_list(list_a: List[Any], n: int) -> Generator[List[int], None, None]:
    """Splits a list passed in chunks with no more, than elements"""
    for x in range(0, len(list_a), n):
        every_chunk = list_a[x : n + x]
        yield every_chunk


def create_file_divided_pages_list(
    file_data: Dict[Any, Any], pagination_threshold: int = PAGINATION_THRESHOLD
) -> List[List[int]]:
    """Creates a list of lists with numbers of file pages"""
    page_quantity = file_data["pages"]
    pages_list = list(range(1, page_quantity + 1))
    result = list(split_list(pages_list, pagination_threshold))
    return result


def generate_file_data(
    file_data: Dict[Any, Any],
    pages: List[int],
    job_id: int,
    output_bucket: Optional[str] = None,
    batch_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Creates init args batches from files data given"""
    converted_file_data = {
        "file": f"{file_data['path']}",
        "bucket": file_data["bucket"],
        "pages": pages,
        "file_id": file_data["id"],
        "output_path": f"runs/{job_id}/{file_data['id']}",
        "datasets": file_data["datasets"],
    }
    if batch_id:
        converted_file_data["output_path"] += f"/{batch_id}"
    if output_bucket and output_bucket != file_data["bucket"]:
        converted_file_data.update({"output_bucket": output_bucket})
    return converted_file_data


async def convert_previous_jobs_for_inference(
    job_ids: List[int],
    session: Session,
    current_tenant: str,
    jw_token: str,
) -> List[Dict[str, Any]]:
    jobs_db = db_service.get_jobs_in_db_by_ids(session, job_ids)
    result = []

    for job in jobs_db:
        if not job.files_ids or not job.all_files_data:
            continue
        converted_files_data = convert_files_data_for_inference(
            job.all_files_data, job.id, current_tenant
        )
        for file_data in converted_files_data:
            output_path = file_data["output_path"].strip()
            _, job_id, file_id, *_ = output_path.split("/")
            revisions = await get_annotation_revisions(
                job_id, file_id, current_tenant, jw_token
            )
            if not revisions:
                continue
            file_data["revision"] = revisions[-1]["revision"]
            file_data["file_id"] = file_id
            result.append(file_data)

    return result


def convert_files_data_for_inference(
    all_files_data: List[Dict[str, Any]],
    job_id: int,
    output_bucket: Optional[str] = None,
    pagination_threshold: int = PAGINATION_THRESHOLD,
) -> List[Dict[str, Any]]:
    """Creates init args from files data to pass it into
    the Inference Pipeline Manager or Annotation microservice"""
    converted_data = []
    for file_data in all_files_data:
        divided_pages_list = create_file_divided_pages_list(
            file_data, pagination_threshold
        )

        if len(divided_pages_list) == 1:
            converted_data.append(
                generate_file_data(
                    file_data,
                    divided_pages_list[0],
                    job_id,
                    output_bucket,
                )
            )
        else:
            for batch_id, pages_list_chunk in enumerate(
                divided_pages_list, start=1
            ):
                converted_data.append(
                    generate_file_data(
                        file_data,
                        pages_list_chunk,
                        job_id,
                        output_bucket,
                        batch_id=batch_id,
                    )
                )

    return converted_data


def convert_files_data_for_annotation(
    all_files_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Converts files data to match Annotation Microservice schema"""
    converted_data = []
    for file_data in all_files_data:
        converted_file_data = {
            "file_id": file_data["id"],
            "pages_number": file_data["pages"],
        }
        converted_data.append(converted_file_data)
    return converted_data


async def get_pipeline_instance_by_its_name(
    pipeline_name: str,
    current_tenant: str,
    jw_token: str,
    pipeline_version: Optional[str] = None,
) -> Any:
    """Gets pipeline instance by its name"""
    params = {"name": pipeline_name}
    if pipeline_version:
        params["version"] = pipeline_version

    logger.info(
        f"Sending request to the pipeline manager to get "
        f"pipeline_id by its name - {pipeline_name} "
        f"and version {pipeline_version}"
    )
    try:
        _, response = await fetch(
            method="GET",
            url=f"{PIPELINES_SERVICE_HOST}/pipeline",
            params=params,
            headers={
                "X-Current-Tenant": current_tenant,
                "Authorization": f"Bearer: {jw_token}",
            },
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(f"Failed request to the Pipeline Manager: {err}")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed request to the Pipeline Manager: {err}",
        )
    return response


class UnsupportedEngine(Exception):
    pass


def files_data_to_pipeline_arg(
    files_data: List[Dict[str, Any]], previous_jobs_data: List[Dict[str, Any]]
) -> Iterator[pipeline.PipelineFile]:
    data = previous_jobs_data if previous_jobs_data else files_data
    for file in data:
        try:
            # todo: change me
            _, job_id, file_id, *_ = file["output_path"].strip().split("/")

            pipeline_file: pipeline.PipelineFile = {
                "bucket": file["bucket"],
                "input": pipeline.PipelineFileInput(job_id=job_id),
                "input_path": file["file"],
                "pages": file["pages"],
                "file_id": file_id,
                "datasets": file["datasets"],
            }
        except KeyError as err:
            logger.exception(f"Unable to process file: {err}")
            raise err
        else:
            rev = file.get("revision")
            if rev:
                pipeline_file["revision"] = rev
            yield pipeline_file


def fill_signed_url(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.debug("Filling signed URL")
    if not JOBS_SIGNED_URL_ENABLED:
        return files

    for file in files:
        file[JOBS_SIGNED_URL_KEY_NAME] = create_pre_signed_s3_url(
            bucket=file["bucket"], path=file["input_path"]
        )

    return files


async def execute_external_pipeline(
    pipeline_id: str,
    pipeline_engine: str,
    job_id: int,
    previous_jobs_data: List[Dict[str, Any]],
    files_data: List[Dict[str, Any]],
    current_tenant: str,
    datasets: List[Dict],
    revisions: List[str],
) -> None:
    logger.info("Running pipeline_engine %s", pipeline_engine)
    kwargs = {
        "pipeline_id": pipeline_id,
        "job_id": job_id,
        "files": fill_signed_url(
            list(files_data_to_pipeline_arg(files_data, previous_jobs_data))
        ),
        "current_tenant": current_tenant,
        "datasets": datasets,
        "revisions": revisions,
    }
    logger.info("Pipeline params: %s", kwargs)
    if pipeline_engine == "airflow":
        pipeline = airflow_utils.AirflowPipeline()
    # return await airflow_utils.run(**kwargs)
    elif pipeline_engine == "databricks":
        pipeline = databricks_utils.DatabricksPipeline()
        # return await databricks_utils.run(**kwargs)
    else:
        raise UnsupportedEngine(f"Unknown engine: {pipeline_engine}")
    return await pipeline.run(**kwargs)


async def execute_pipeline(
    pipeline_id: Union[int, str],
    job_id: int,
    files_data: List[Dict[str, Any]],
    current_tenant: str,
    jw_token: str,
) -> None:
    """Executes Run in the Inference Pipeline Manager"""
    if ROOT_PATH:
        webhook = f"{JOBS_SERVICE_HOST}/{ROOT_PATH}/jobs"
    else:
        webhook = f"{JOBS_SERVICE_HOST}/jobs"

    params = {
        "job_id": job_id,
        "webhook": webhook,
    }
    logger.info(
        f"Job id = {job_id}. Sending request to the pipeline manager."
        f" Callback_URI: {webhook}"
    )
    try:
        _, response = await fetch(
            method="POST",
            url=f"{PIPELINES_SERVICE_HOST}/pipelines/{pipeline_id}/execute",
            headers={
                "X-Current-Tenant": current_tenant,
                "Authorization": f"Bearer: {jw_token}",
            },
            params=params,
            body=files_data,
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(f"Failed request to the Pipeline Manager: {err}")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed request to the Pipeline Manager: {err}",
        )
    return None


async def execute_in_annotation_microservice(
    created_job: CombinedJob,
    jw_token: str,
    current_tenant: str,
    previous_jobs_data: List[Dict[str, Any]] = None,
) -> None:
    """Sends specifically formatted files data to the Annotation Microservice
    and triggers tasks creation in it"""
    job_id = created_job.id

    # if ROOT_PATH:
    #     callback_url = f"{JOBS_SERVICE_HOST}/{ROOT_PATH}/jobs/{job_id}"
    # else:
    callback_url = f"{JOBS_SERVICE_HOST}/jobs/{job_id}"

    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {jw_token}",
    }
    json = {
        "job_type": created_job.type,
        "name": created_job.name,
        "callback_url": callback_url,
        "owners": created_job.owners,
        "annotators": created_job.annotators,
        "validators": created_job.validators,
        "files": created_job.files,
        "datasets": created_job.datasets,
        "previous_jobs": previous_jobs_data or [],
        "categories": created_job.categories,
        "deadline": fastapi.encoders.jsonable_encoder(created_job.deadline),
        "extensive_coverage": created_job.extensive_coverage,
        "revisions": created_job.revisions,
    }
    if created_job.validation_type:
        json["validation_type"] = created_job.validation_type
    if created_job.is_auto_distribution:
        json["is_auto_distribution"] = created_job.is_auto_distribution
    logger.info(
        f"Job id = {job_id}. Sending request to annotation manager. "
        f" Callback URI is {callback_url}, headers={headers}, "
        f"params sent = {json}"
    )
    # --------- request to an annotation microservice ---------- #
    try:
        _, response = await fetch(
            method="POST",
            url=f"{ANNOTATION_SERVICE_HOST}/jobs/{job_id}",
            headers=headers,
            body=json,
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(f"Failed request to the Annotation Manager: {err}")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed request to the Annotation Manager: {err}",
        )
    # ----------------------------------------------------------------- #
    return None


def delete_duplicates(
    files_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Delete duplicates"""
    used_file_ids = set()

    for i in range(len(files_data) - 1, -1, -1):
        if files_data[i]["id"] in used_file_ids:
            del files_data[i]
        else:
            used_file_ids.add(files_data[i]["id"])

    return files_data


def pick_params_for_annotation(
    new_job_params: JobParamsToChange,
) -> AnnotationJobUpdateParamsInAnnotation:
    picked_params = AnnotationJobUpdateParamsInAnnotation.parse_obj(
        new_job_params
    )
    return picked_params


async def start_job_in_annotation(
    job_id: int,
    current_tenant: str,
    jwt_token: str,
) -> None:
    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {jwt_token}",
    }

    logger.info(
        f"Job id = {job_id}. Sending request to start "
        f"job in annotation manager."
        f"Headers={headers}"
    )
    try:
        _, response = await fetch(
            method="POST",
            url=f"{ANNOTATION_SERVICE_HOST}/jobs/{job_id}/start",
            headers=headers,
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(
            "Failed request to the Annotation Manager: {}".format(err)
        )
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed request to the Annotation Manager: {}".format(err),
        )


async def update_job_in_annotation(
    job_id: int,
    new_job_params_for_annotation: AnnotationJobUpdateParamsInAnnotation,
    current_tenant: str,
    jw_token: str,
) -> Dict[str, Any]:
    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {jw_token}",
    }
    json_data = new_job_params_for_annotation.dict(exclude_defaults=True)
    logger.info(
        f"Job id = {job_id}. Sending request to update "
        f"job in annotation manager. "
        f" Headers={headers}, params sent = {json_data}"
    )
    try:
        _, changed_params = await fetch(
            method="PATCH",
            url=f"{ANNOTATION_SERVICE_HOST}/jobs/{job_id}",
            headers=headers,
            body=json_data,
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(f"Failed request to the Annotation Manager: {err}")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed request to the Annotation Manager: {err}",
        )
    return {key: value for key, value in changed_params.items() if value}


async def get_job_progress(
    job_id: int,
    session: Session,
    current_tenant: Optional[str],
    jw_token: str,
    api_client: client.ApiClient,
) -> Optional[Dict[str, int]]:
    """Get progress of the job with 'job_id' from Pipelines
    or Annotation Manager depending on 'job_mode'."""
    job = db_service.get_job_in_db_by_id(session, job_id)
    if job is None:
        logger.warning(f"job with id={job_id} not present in the database.")
        return None

    url = f"{ANNOTATION_SERVICE_HOST}/jobs/{job_id}/progress"
    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {jw_token}",
    }

    timeout = aiohttp.ClientTimeout(total=5)

    try:
        _, response = await fetch(
            method="GET", url=url, headers=headers, timeout=timeout
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(f"Failed request url = {url}, error = {err}")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed request to the Annotation Manager: {err}",
        )
    
    response.update({"mode": str(job.mode)})

    if job.type in [JobType.AnnotationJob, JobType.ExtractionJob, JobType.ExtractionWithAnnotationJob]:
        await update_job_status_by_type(session, job, response, job_id, api_client)
        return response

    logger.warning(
        f"Unknown job type: {job.type}, treating as manual by default."
    )
    await update_manual_job_status(session, job, response)
    return response


async def update_job_status_by_type(
    session: Session,
    job: CombinedJob,
    response: Dict[str, int],
    job_id: int,
    api_client: client.ApiClient,
) -> None:
    job_type = job.type

    if job_type in [JobType.AnnotationJob, JobType.ExtractionWithAnnotationJob]:
        await update_manual_job_status(session, job, response)
    
    else: # JobType.ExtractionJob
        await handle_pipeline_driven_job(
            session, job, response, job_id, api_client
        )


async def update_manual_job_status(
    session: Session, job: CombinedJob, response: Dict[str, int]
) -> None:
    """Update the job status based on the number of completed tasks in the response.

    If 'finished' > 0:
    - Set status to 'finished' if all tasks are done.
    - Set status to 'in_progress' if some tasks are done.
    Otherwise, the job status remains unchanged.
    """
    finished = response.get("finished")
    total = response.get("total")

    if finished is None or total is None:
        logger.warning("Missing keys in response for job %s", job.id)
        return

    if finished == 0: # If no tasks are completed, the job will remain in a pending state.
        return

    if finished == total:
        db_service.update_job_status(session, job, Status.finished)
    else:
        db_service.update_job_status(session, job, Status.in_progress)


async def handle_pipeline_driven_job(
    session: Session,
    job: CombinedJob,
    response: Dict[str, int],
    job_id: int,
    api_client: client.ApiClient,
) -> None:
    """Handle Extraction jobs that depend on pipeline execution."""
    pipeline_id = job.pipeline_id
    dag_run_id = f"{pipeline_id}:{job_id}"
    # To display progress for extraction jobs, response["total"] will always be 1. The value of response["finished"] will be either 0 or 1, indicating whether the pipeline has completed successfully.
    response["total"] = 1

    # Activate the pipeline if it’s not already active, this will ensure the pipeline is running.
    await activate_pipeline(pipeline_id, api_client)

    pipeline_status = await fetch_pipeline_status(pipeline_id, dag_run_id, api_client)

    if pipeline_status == AirflowPipelineStatus.success.value:
        db_service.update_job_status(session, job, Status.finished)
        response["finished"] = 1
    elif pipeline_status == AirflowPipelineStatus.failed.value:
        db_service.update_job_status(session, job, Status.failed)
        response["finished"] = 0
    elif pipeline_status == AirflowPipelineStatus.running.value:
        db_service.update_job_status(session, job, Status.in_progress)
        response["finished"] = 0
    else:
        logger.warning(f"Unexpected pipeline status '{pipeline_status}' for job {job_id}")


async def fetch_pipeline_status(
    pipeline_id: str,
    dag_run_id: str,
    api_client: client.ApiClient,
) -> bool:
    try:
        result = await airflow_utils.fetch_dag_status(
            pipeline_id,
            dag_run_id,
            api_client=api_client,
        )
    except RuntimeError as e:
        logger.exception(
            f"Runtime error occurred while fetching pipeline status: {e}"
        )
        raise fastapi.HTTPException(
            status_code=500, detail=f"Failed to fetch pipeline status."
        )
    return result


async def activate_pipeline(
    pipeline_id: str, api_client: client.ApiClient
) -> None:
    try:
        await airflow_utils.activate_dag(pipeline_id, api_client)
    except RuntimeError as e:
        logger.exception(f"Failed to activate DAG: {e}")
        raise fastapi.HTTPException(
            status_code=500, detail=f"Failed to activate pipline"
        )


async def fetch(
    method: str,
    url: str,
    body: Optional[Any] = None,
    data: Optional[Any] = None,
    headers: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Tuple[int, Any]:
    async with aiohttp.request(
        method=method, url=url, json=body, headers=headers, data=data, **kwargs
    ) as resp:
        status_ = resp.status
        json = {}
        if status_ != fastapi.status.HTTP_204_NO_CONTENT:
            json = await resp.json()
        return status_, json


def get_test_db_url(main_db_url: str) -> str:
    """
    Takes main database url and returns test database url.

    Example:
    postgresql+psycopg2://admin:admin@host:5432/service_name ->
    postgresql+psycopg2://admin:admin@host:5432/test_db
    """
    main_db_url_split = main_db_url.split("/")
    main_db_url_split[-1] = "test_db"
    result = "/".join(main_db_url_split)
    return result


async def send_category_taxonomy_link(
    current_tenant: str,
    jwt_token: str,
    taxonomy_link_params: List[CategoryLinkParams],
) -> None:
    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {jwt_token}",
    }
    try:
        _, response = await fetch(
            method="POST",
            url=f"{TAXONOMY_SERVICE_HOST}/taxonomy/link_category",
            headers=headers,
            body=[
                taxonomy_link_param.dict(exclude_defaults=True)
                for taxonomy_link_param in taxonomy_link_params
            ],
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception("Failed send category link to taxonomy")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed send category link to taxonomy: {err}",
        )


async def delete_taxonomy_link(
    job_id: str,
    current_tenant: str,
    jwt_token: str,
) -> None:
    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {jwt_token}",
    }
    try:
        _, response = await fetch(
            method="DELETE",
            url=f"{TAXONOMY_SERVICE_HOST}/taxonomy/link_category/{job_id}",
            headers=headers,
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception("Failed delete taxonomy link")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed delete taxonomy link: {err}",
        )


def get_categories_ids(
    categories: List[Union[str, CategoryLinkInput]],
) -> Tuple[List[str], List[CategoryLinkInput]]:
    categories_ids = [
        category_id
        for category_id in categories
        if isinstance(category_id, str)
    ]
    categories_links = [
        category_link
        for category_link in categories
        if isinstance(category_link, CategoryLinkInput)
    ]
    categories_links_ids = [
        category_link.category_id for category_link in categories_links
    ]
    return categories_ids + categories_links_ids, categories_links


def get_taxonomy_links(
    job_id: str, categories_links: List[CategoryLinkInput]
) -> List[CategoryLinkParams]:
    return [
        CategoryLinkParams(
            job_id=job_id,
            category_id=category_link.category_id,
            taxonomy_id=category_link.taxonomy_id,
            taxonomy_version=category_link.taxonomy_version,
        )
        for category_link in categories_links
    ]


async def get_annotator_username(
    job_annotator_uuid: str, current_tenant: str, token: str
) -> str:
    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {token}",
    }
    try:
        _, user_data = await fetch(
            method="GET",
            url=f"{USERS_HOST}/users/{job_annotator_uuid}",
            headers=headers,
            raise_for_status=True,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(
            "Failed getting user data for annotator - %s", job_annotator_uuid
        )
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed getting user data for annotator - "
            f"{job_annotator_uuid}: {err}",
        )
    return user_data["username"]


async def enrich_annotators_with_usernames(
    job_obj: CombinedJob, current_tenant: str, token: str
) -> CombinedJob:
    logger.info("Enriching job_obj with usernames of annotators")
    job_annotators = job_obj.annotators
    logger.info("job_annotators = %s", job_annotators)

    if not job_annotators:
        return job_obj

    reformatted_job_annotators = []
    for job_annotator_id in job_annotators:
        logger.info("job_annotator_id = %s", job_annotator_id)
        job_annotator_username = await get_annotator_username(
            job_annotator_id, current_tenant, token
        )
        logger.info("job_annotator_username got = %s", job_annotator_username)

        reformatted_job_annotators.append(
            {"id": job_annotator_id, "username": job_annotator_username}
        )

    job_obj.annotators = reformatted_job_annotators
    return job_obj


async def get_annotation_revisions(
    job_id: int, file_id: int, current_tenant: Optional[str], jw_token: str
) -> Optional[List[dict]]:
    """Get progress of the job with 'job_id' from Pipelines
    or Annotation Manager depending on 'job_mode'."""

    headers = {
        "X-Current-Tenant": current_tenant,
        "Authorization": f"Bearer: {jw_token}",
    }
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        _, response = await fetch(
            method="GET",
            url=f"{ANNOTATION_SERVICE_HOST}/revisions/{job_id}/{file_id}",
            headers=headers,
            timeout=timeout,
        )
    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(
            f"Failed request to get revisions "
            f"for job_id = {job_id}, file_id = {file_id}"
        )
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed request to the Annotation Manager: {err}",
        )

    return response


async def search_datasets_by_ids(
    datasets_ids: List[int], current_tenant: str, jw_token: str
) -> Dict[str, Any]:
    """Search datasets by a list of IDs.
    Returns a list of datasets that match the given IDs."""

    try:
        logger.info(
            f"Sending request to the dataset manager "
            f"to search datasets by IDs: {datasets_ids}"
        )
        status, response = await fetch(
            method="POST",
            url=f"{ASSETS_SERVICE_HOST}/datasets/search",
            headers={
                "X-Current-Tenant": current_tenant,
                "Authorization": f"Bearer {jw_token}",
            },
            body={
                "filters": [
                    {"field": "id", "operator": "in", "value": datasets_ids}
                ],
            },
            raise_for_status=True,
        )
        if status == 404:
            logger.error(
                f"Failed to find datasets: {datasets_ids}, resp: {response}"
            )
            return {}

    except aiohttp.client_exceptions.ClientError as err:
        logger.exception(f"Failed request to get datasets info: {err}")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed request to get datasets info: {err}",
        )

    return response


async def validate_create_job_files(db: Session, file_ids: List[int]):
    """Validate job's files if they all exist in database"""
    matched_jobs_in_db = db_service.get_jobs_in_db_by_ids(db, file_ids)
    if len(file_ids) > len(matched_jobs_in_db):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Some of these files do not exist",
        )


async def validate_create_job_name(db: Session, job_name: str):
    """Check if the job name is already taken"""
    existing_jobs_by_name = db_service.get_jobs_by_name(db, job_name)
    if len(existing_jobs_by_name) > 0:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"The job name '{job_name}' is already being used",
        )


async def validate_create_job_previous_jobs(
    db: Session, previous_jobs_ids: List[int]
) -> List[int]:
    """validate given previous job ids in database, return the found ids"""
    previous_jobs = db_service.get_jobs_in_db_by_ids(db, previous_jobs_ids)
    if not previous_jobs:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Jobs with these ids do not exist.",
        )
    return [j.id for j in previous_jobs]
