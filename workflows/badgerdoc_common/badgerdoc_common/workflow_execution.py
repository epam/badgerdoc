import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Any, TypeVar

from temporalio import workflow

logger = logging.getLogger(__name__)


class WorkflowStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class BadgerdocWorkflowResult:
    workflow_id: str
    status: WorkflowStatus
    result: Any = None
    status_message: str | None = None


@dataclass
class BadgerdocWorkflowParams:
    workflow_type: str
    task_queue: str
    workflow_id: str
    workflow_input: Any = None
    execution_timeout: int | None = None
    random_postfix: bool = False


async def run_child_workflow(params: BadgerdocWorkflowParams) -> str:
    workflow_id = params.workflow_id

    execution_timeout = None
    if params.execution_timeout is not None:
        execution_timeout = timedelta(seconds=params.execution_timeout)

    started_workflow = await workflow.start_child_workflow(
        params.workflow_type,
        params.workflow_input,
        id=workflow_id,
        task_queue=params.task_queue,
        execution_timeout=execution_timeout,
    )

    return started_workflow


async def wait_for_workflows_concurrent(
    started_workflow_handles: list[workflow.ChildWorkflowHandle[Any, Any]],
) -> list[BadgerdocWorkflowResult]:
    logger.info(
        "Waiting for %d workflows to complete concurrently",
        len(started_workflow_handles),
    )
    workflow_results = await asyncio.gather(*started_workflow_handles)
    return workflow_results


T = TypeVar("T")


async def wait_for_workflows_concurrent_t(
    started_workflow_handles: list[workflow.ChildWorkflowHandle[Any, Any]],
    result_type: type[T],
) -> list[T]:

    logger.info(
        "Waiting for %d workflows to complete concurrently (typed)",
        len(started_workflow_handles),
    )
    workflow_results = await asyncio.gather(*started_workflow_handles)

    typed_results = []
    for result in workflow_results:
        typed_results.append(result_type(**result))

    return typed_results
