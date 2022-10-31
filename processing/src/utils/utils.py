from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar
from urllib.parse import urljoin

from cache import AsyncTTL
from sqlalchemy.orm import Session

from src import db, schema
from src.config import settings
from src.utils.aiohttp_utils import send_request
from src.utils.logger import get_log_exception_msg, get_logger

logger = get_logger(__name__)
T = TypeVar("T")


def get_internal_url(url: str) -> str:
    return url.rstrip(settings.external_postfix)


def split_iterable(list_a: List[T], chunk_size: int) -> List[List[T]]:
    """Splits a list passed in chunks with no more, than elements"""
    return [
        list_a[x : chunk_size + x] for x in range(0, len(list_a), chunk_size)
    ]


@AsyncTTL(time_to_live=60 * 5, maxsize=8)
async def get_model_url(model_id: str) -> str:
    logger.info("Getting %s's url from `models`", model_id)
    if settings.preprocessing_url:
        logger.warning("Model url is predefined in the config.")
        return settings.preprocessing_url

    models_service_url = urljoin(settings.host_models, model_id)
    models_response = await send_request("GET", models_service_url)
    try:
        return get_internal_url(str(models_response.json["url"]))
    except KeyError as err:
        logger.error(
            "Error while getting model url. No `url` key. Model_id=%s Traceback: `%s`. ",
            model_id,
            get_log_exception_msg(err),
        )
        raise err


async def get_files_data(
    files_ids: List[int], current_tenant: str, jw_token: str
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """Takes ids of files from request body.
    Returns list of dictionaries with data for each file
    with ids passed in request_body"""
    elements_per_page_in_dataset_manager = 100
    splatted_files_ids = split_iterable(
        files_ids, elements_per_page_in_dataset_manager
    )
    all_files_data = []
    for batch in splatted_files_ids:
        params = {
            "pagination": {
                "page_num": len(files_ids)
                // elements_per_page_in_dataset_manager
                + 1,
                "page_size": elements_per_page_in_dataset_manager,
            },
            "filters": [{"field": "id", "operator": "in", "value": batch}],
        }
        assets_url = f"{settings.host_assets}/files/search"
        logger.info("sending request to %s", assets_url)
        files_data = (
            await send_request(
                "POST",
                url=assets_url,
                json=params,
                headers={
                    "X-Current-Tenant": current_tenant,
                    "Authorization": f"Bearer {jw_token}",
                },
            )
        ).json

        for file_data in files_data["data"]:
            all_files_data.append(file_data)

    valid_files_uuids = [file_data["id"] for file_data in all_files_data]

    return all_files_data, valid_files_uuids


async def execute_pipeline(
    pipeline_id: int,
    files_data: Iterable[Dict[str, Any]],
    current_tenant: str,
    jw_token: str,
    session: Session,
    batch_id: str,
    args: Optional[Dict[str, Any]],
) -> None:
    data = []
    tasks = []

    for file in files_data:
        body = {
            "input_path": None,
            "input": args,
            "file": file["path"],
            "bucket": file["bucket"],
            "pages": file["pages"],
            "output_path": file["output_path"],
            "output_bucket": file["bucket"],
        }
        data.append(body)
        task = db.models.DbPreprocessingTask(
            file_id=file["id"],
            status=schema.Status.PEND,
            execution_args=body,
            pipeline_id=pipeline_id,
            batch_id=batch_id,
        )
        tasks.append(task)

    pipeline_url = f"{settings.host_pipelines}/pipelines/{pipeline_id}/execute"
    webhook = settings.get_webhook("tasks")
    logger.info("sending request to %s", pipeline_url)

    res = await send_request(
        "POST",
        pipeline_url,
        headers={
            "X-Current-Tenant": current_tenant,
            "Authorization": f"Bearer: {jw_token}",
        },
        json=data,
        params={"webhook": webhook},
    )

    tasks_ids = (task.get("id") for task in res.json)
    for task, execution_id in zip(tasks, tasks_ids):
        task.execution_id = execution_id

    session.add_all(tasks)
    session.commit()


def map_finish_status_for_assets(
    status: schema.Status,
) -> schema.PreprocessingStatus:
    if status == schema.Status.DONE:
        return schema.PreprocessingStatus.PREPROCESSED
    if status == schema.Status.FAIL:
        return schema.PreprocessingStatus.FAILED
    if status == schema.Status.RUN:
        return schema.PreprocessingStatus.PREPROCESSING_IN_PROGRESS
    raise ValueError("invalid status argument")
