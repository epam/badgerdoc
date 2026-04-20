import logging
from urllib.parse import urlencode

from temporalio import activity

from badgerdoc_common import badgerdoc_event, badgerdoc_http

logger = logging.getLogger(__name__)


@activity.defn
async def badgerdoc_get_workflows(
    request_data: badgerdoc_event.BadgerdocEvent,
) -> list[badgerdoc_event.BadgerdocWorkflow]:

    logger.info("Executing badgerdoc_get_workflows activity")
    workflows = []
    params = {
        "event_entity": request_data.event_entity,
        "event_type": request_data.event_type,
        "is_active": "true",
        "trigger": "automatic",
    }
    endpoint = f"/badgerdoc/workflow-registry/?{urlencode(params)}"

    for workflow_data in await badgerdoc_http.badgerdoc_get(endpoint):
        logger.info("Workflow data: %s", workflow_data)
        try:
            workflow = badgerdoc_event.BadgerdocWorkflow(**workflow_data)
        except KeyError:
            logger.exception(
                "Missing key in workflow data in workflow: %s", workflow_data
            )
            continue
        workflows.append(workflow)
    return workflows


@activity.defn
async def badgerdoc_get_workflow_by_id(
    workflow_registry_id: int,
) -> badgerdoc_event.BadgerdocWorkflow:
    logger.info(
        "Executing badgerdoc_get_workflow_by_id activity for ID: %s",
        workflow_registry_id,
    )

    endpoint = f"/badgerdoc/workflow-registry/{workflow_registry_id}/"

    workflow_data = await badgerdoc_http.badgerdoc_get(endpoint)
    logger.info("Workflow data: %s", workflow_data)

    try:
        workflow = badgerdoc_event.BadgerdocWorkflow(**workflow_data)

        if not workflow_data.get("is_active", False):
            raise ValueError(f"Workflow {workflow_registry_id} is not active")

        return workflow
    except KeyError as e:
        logger.exception("Missing key in workflow data: %s", workflow_data)
        raise ValueError(
            f"Invalid workflow data for ID {workflow_registry_id}: missing field {e}"
        )
