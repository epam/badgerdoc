import logging
from typing import Any

from temporalio import activity

from badgerdoc_common import badgerdoc_http

logger = logging.getLogger(__name__)


@activity.defn
async def write_agent_log(
    document_id: int,
    task_id: int | None,
    level: str,
    source: str,
    log: dict[str, Any],
) -> None:
    payload: dict[str, Any] = {
        "document": document_id,
        "task": task_id,
        "level": level,
        "source": source,
        "log": log,
    }
    try:
        await badgerdoc_http.badgerdoc_post("/badgerdoc/agent-log/", payload)
    except Exception:
        logger.exception("Failed to write agent log to Badgerdoc")
