import asyncio
import logging

from temporalio import activity

from badgerdoc_common import badgerdoc_http

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = {"Finished", "Failed", "Not Found"}
_POLL_INTERVAL_SECONDS = 5
_MAX_POLL_ATTEMPTS = 360  # 30 minutes at 5s intervals


@activity.defn
async def wait_for_triggered_workflows(
    workflow_results: list[dict],
) -> list[dict]:
    """Poll each triggered workflow until it reaches a terminal status.

    Returns the same workflow_results list, enriched with a ``final_status``
    key for each entry, so downstream activities can inspect which ones
    succeeded.
    """
    workflow_ids = [
        str(entry["workflow_id"])
        for entry in workflow_results
        if entry.get("workflow_id")
    ]

    if not workflow_ids:
        logger.warning("No workflow_ids to wait for")
        return workflow_results

    pending: dict[str, int] = {wf_id: 0 for wf_id in workflow_ids}

    while pending:
        activity.heartbeat()

        for wf_id in list(pending.keys()):
            attempt = pending[wf_id]
            if attempt >= _MAX_POLL_ATTEMPTS:
                logger.warning(
                    "Giving up waiting for workflow %s after %d attempts",
                    wf_id,
                    attempt,
                )
                del pending[wf_id]
                continue

            try:
                response = await badgerdoc_http.badgerdoc_get(
                    f"/badgerdoc/workflow-registry/workflow/status/{wf_id}/"
                )
                status = response.get("status", "Not Found") if isinstance(response, dict) else "Not Found"
            except Exception:
                logger.exception(
                    "Failed to poll status for workflow %s", wf_id
                )
                status = "Not Found"

            logger.info(
                "Workflow %s status: %s (attempt %d)", wf_id, status, attempt
            )

            if status in _TERMINAL_STATUSES:
                del pending[wf_id]
            else:
                pending[wf_id] = attempt + 1

        if pending:
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

    # Annotate results with their final status for logging/observability.
    id_set = set(workflow_ids)
    for entry in workflow_results:
        if entry.get("workflow_id") not in id_set:
            entry.setdefault("final_status", "skipped")

    logger.info("All triggered workflows reached terminal status")
    return workflow_results
