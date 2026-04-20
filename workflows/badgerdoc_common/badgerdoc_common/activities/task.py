import logging
from dataclasses import dataclass
from typing import Any

from temporalio import activity

from badgerdoc_common import badgerdoc_http
from badgerdoc_common.activities import extraction, task_status

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocTask:
    id: int
    status: task_status.BadgerdocTaskStatus
    document_id: int
    extractions: list["extraction.BadgerdocExtraction"]


@dataclass
class BadgerdocTaskCreateRequest:
    status_id: int | None = None
    document_id: int | None = None
    extraction_ids: list[int] | None = None


def _parse_task_response_body(response_data: dict[str, Any]) -> BadgerdocTask:
    task_id = response_data.get("id")
    if task_id is None:
        raise ValueError("Task creation succeeded but no task ID returned")

    return BadgerdocTask(
        id=task_id,
        status=task_status.BadgerdocTaskStatus(
            id=response_data["status"]["id"],
            name=response_data["status"]["name"],
            order=response_data["status"]["order"],
        ),
        document_id=response_data["document"]["id"],
        extractions=[
            extraction.BadgerdocExtraction(
                id=extraction_data["id"],
                document_id=extraction_data["document_id"],
                created_by=extraction_data["created_by"],
                status=extraction_data["status"],
                temporal_job_id=extraction_data.get("temporal_job_id"),
                comment=extraction_data.get("comment"),
                tags=extraction_data.get("tags") or [],
            )
            for extraction_data in response_data["extractions"]
        ],
    )


@activity.defn
async def badgerdoc_create_task(
    task_data: BadgerdocTaskCreateRequest,
) -> BadgerdocTask:
    logger.info(
        "Creating task in Badgerdoc: status=%s, document=%d",
        task_data.status_id,
        task_data.document_id,
    )

    fields_dict = {
        "status": task_data.status_id,
        "document": task_data.document_id,
    }
    payload = {
        key: value for key, value in fields_dict.items() if value is not None
    }

    response_data = await badgerdoc_http.badgerdoc_post(
        "/badgerdoc/task/", payload
    )

    task = _parse_task_response_body(response_data)
    logger.info("Successfully created task with ID: %d", task.id)
    return task


@dataclass
class BadgerdocTaskUpdateRequest:
    id: int
    status_id: int | None = None
    extraction_ids: list[int] | None = None


@activity.defn
async def badgerdoc_update_task(
    task_data: BadgerdocTaskUpdateRequest,
) -> BadgerdocTask:
    fields_dict = {
        "status": task_data.status_id,
        "extractions": task_data.extraction_ids,
    }
    payload = {
        key: value for key, value in fields_dict.items() if value is not None
    }
    response_data = await badgerdoc_http.badgerdoc_patch(
        f"/badgerdoc/task/{task_data.id}/", payload
    )
    task = _parse_task_response_body(response_data)
    logger.info("Successfully updated task with ID: %d", task.id)
    return task


@activity.defn
async def badgerdoc_list_next_task_statuses(
    task: BadgerdocTask,
) -> list[task_status.BadgerdocTaskStatus]:
    return await task_status.badgerdoc_list_next_statuses(task.status.id)


@activity.defn
async def badgerdoc_get_task(task_id: int) -> BadgerdocTask:
    logger.info("Getting task from Badgerdoc: task_id=%d", task_id)

    response_data = await badgerdoc_http.badgerdoc_get(
        f"/badgerdoc/task/{task_id}/details/"
    )

    task = _parse_task_response_body(response_data)
    logger.info("Successfully retrieved task with ID: %d", task.id)
    return task
