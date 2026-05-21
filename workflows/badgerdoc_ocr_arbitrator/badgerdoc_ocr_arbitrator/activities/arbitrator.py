import logging

from temporalio import activity

from badgerdoc_common import badgerdoc_event, badgerdoc_http, trigger
from badgerdoc_common.activities import agent_log, workflow_registry
from badgerdoc_ocr_arbitrator.arbitrator_agent import (
    ArbitratorAgent,
)

logger = logging.getLogger(__name__)


async def get_existing_workflows() -> list[badgerdoc_event.BadgerdocWorkflow]:
    params = {
        "is_active": True,
        "trigger": "manual",
        "tags": "ai-inference",
    }
    workflows = await workflow_registry.badgerdoc_get_workflows(params)
    if workflows:
        return workflows
    return []


async def build_engine_to_id_mapping() -> dict[str, int]:
    """Builds a mapping of engine names to workflow IDs"""
    workflows = await get_existing_workflows()
    engine_map: dict[str, int] = {}
    for workflow_data in workflows:
        engine_map[workflow_data.name] = workflow_data.id
    return engine_map


@activity.defn
async def start_arbitrator(
    params: trigger.DocumentTriggerParams,
) -> list[dict[str, int | str]]:
    logger.info("Starting start_arbitrator activity")

    document_id = params.original_document.id
    task_id = params.original_task.id if params.original_task else None
    await agent_log.write_agent_log(
        document_id,
        task_id,
        "INFO",
        "Temporal",
        {"message": "Looking for agents"},
    )

    llm_params = params.llm_params or ""
    linked_document_pages = params.linked_document_pages or []

    agent = ArbitratorAgent()

    ids = await agent.get_target_workflows(
        llm_params=llm_params,
        mapping_tool=build_engine_to_id_mapping,
    )

    all_workflows = await get_existing_workflows()
    logger.info("Got ids: %s", ids)
    logger.info("Mapping: %s", await build_engine_to_id_mapping())
    selected_workflows = [w for w in all_workflows if w.id in ids]
    # to avoide recursion
    workflows = [w for w in selected_workflows if w.id != params.workflow.id]

    if not workflows:
        logger.warning("No workflows selected by arbitrator agent")
        await agent_log.write_agent_log(
            document_id,
            task_id,
            "WARNING",
            "Temporal",
            {"message": "No agents found. Check logs for more information"},
        )
        return []

    document_ids: set[int] = {params.original_document.id}
    document_ids.update(
        page.document.id
        for page in linked_document_pages
        if page.document and page.document.id
    )

    started_extractions: list[dict[str, int | str]] = []

    await agent_log.write_agent_log(
        document_id,
        task_id,
        "INFO",
        "Temporal",
        {"message": f"Found agents: {[w.name for w in workflows]}"},
    )

    for workflow_data in workflows:
        engine_name = next(
            (
                tag
                for tag in (workflow_data.tags or [])
                if tag and tag != "ai-inference"
            ),
            workflow_data.name or str(workflow_data.id),
        )

        for document_id in sorted(document_ids):
            endpoint = f"/badgerdoc/workflow-registry/manual-trigger/{workflow_data.id}/"
            payload = {
                "document_id": document_id,
                "llm_params": llm_params,
            }
            if params.original_task:
                payload["task_id"] = params.original_task.id

            response_data = await badgerdoc_http.badgerdoc_post(
                endpoint, payload
            )
            await agent_log.write_agent_log(
                document_id,
                task_id,
                "INFO",
                "Temporal",
                {"message": f"Agent started: {workflow_data.name}"},
            )
            started_workflow_id = response_data.get("workflow_id")
            workflow_input_data = response_data.get("workflow_input_data")
            if isinstance(workflow_input_data, dict):
                target_extraction = workflow_input_data.get(
                    "target_extraction"
                )
                if isinstance(target_extraction, dict):
                    target_extraction_id = target_extraction.get("id")
                    if isinstance(target_extraction_id, int):
                        started_extractions.append(
                            {
                                "extraction_id": target_extraction_id,
                                "engine_name": engine_name,
                                "workflow_id": started_workflow_id,
                            }
                        )
            logger.info(
                "Triggered workflow_registry_id=%s for document_id=%s, response=%s",
                workflow_data.id,
                document_id,
                response_data,
            )

    return started_extractions
