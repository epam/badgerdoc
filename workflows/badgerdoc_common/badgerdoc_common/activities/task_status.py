import logging
from dataclasses import dataclass
from typing import Any

from temporalio import activity
from temporalio.exceptions import ApplicationError

from badgerdoc_common import badgerdoc_http

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocTaskStatus:
    id: int
    name: str
    order: int


def parse_task_status_list(response_data: Any) -> list[BadgerdocTaskStatus]:
    if not isinstance(response_data, list):
        raise ApplicationError(
            f"Expected response to be a list, got {type(response_data)} instead: {response_data}"
        )

    statuses: list[BadgerdocTaskStatus] = []
    for status_data in response_data:
        logger.debug("Task status: %s", status_data)
        try:
            status = BadgerdocTaskStatus(
                id=status_data["id"],
                name=status_data["name"],
                order=status_data["order"],
            )
        except KeyError:
            logger.warning("Missing key in status data: %s", status_data)
            raise

        statuses.append(status)

    return statuses


@activity.defn
async def badgerdoc_list_task_statuses() -> list[BadgerdocTaskStatus]:
    response_data = await badgerdoc_http.badgerdoc_get(
        "/badgerdoc/task/status/"
    )
    return parse_task_status_list(response_data)


@activity.defn
async def badgerdoc_list_next_statuses(
    task_status_id: int,
) -> list[BadgerdocTaskStatus]:
    response_data = await badgerdoc_http.badgerdoc_get(
        f"/badgerdoc/task/status/next/{task_status_id}/"
    )
    return parse_task_status_list(response_data)
