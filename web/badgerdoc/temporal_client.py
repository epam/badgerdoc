import asyncio
import logging
import os
from enum import StrEnum
from typing import Any

from temporalio.client import Client, WorkflowExecutionStatus

logger = logging.getLogger(__name__)


class TemporalWorkflowStatus(StrEnum):
    IN_PROGRESS = "In Progress"
    FINISHED = "Finished"
    FAILED = "Failed"
    NOT_FOUND = "Not Found"


async def get_temporal_client() -> Client:
    try:
        target_host = os.getenv("TEMPORAL_ADDRESS", "")
        temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
        logger.debug(
            "Connecting to Temporal server at %s, namespace: %s",
            target_host,
            temporal_namespace,
        )

        client = await Client.connect(
            target_host=target_host,
            namespace=temporal_namespace,
        )
        return client
    except Exception as e:
        logger.exception("Failed to connect to Temporal server: %s", e)
        raise


async def a_start_workflow(
    workflow_type: str,
    task_queue: str,
    workflow_id: str,
    args: list[Any],
) -> str:
    client = await get_temporal_client()
    handle = await client.start_workflow(
        workflow=workflow_type,
        task_queue=task_queue,
        id=workflow_id,
        args=args,
    )
    return handle.id


def start_workflow(
    workflow_type: str,
    task_queue: str,
    workflow_id: str,
    args: list[Any],
) -> str:
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            a_start_workflow(workflow_type, task_queue, workflow_id, args)
        )
    except RuntimeError:
        return asyncio.run(
            a_start_workflow(workflow_type, task_queue, workflow_id, args)
        )


async def a_get_workflow_status(workflow_id: str) -> TemporalWorkflowStatus:
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)

    try:
        description = await handle.describe()
        status = description.status
        if status == WorkflowExecutionStatus.RUNNING:
            return TemporalWorkflowStatus.IN_PROGRESS

        if status == WorkflowExecutionStatus.COMPLETED:
            return TemporalWorkflowStatus.FINISHED

        return TemporalWorkflowStatus.FAILED
    except Exception:
        return TemporalWorkflowStatus.NOT_FOUND


def get_workflow_status(
    workflow_id: str,
) -> TemporalWorkflowStatus:
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(a_get_workflow_status(workflow_id))
    except RuntimeError:
        return asyncio.run(a_get_workflow_status(workflow_id))
