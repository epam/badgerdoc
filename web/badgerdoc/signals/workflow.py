import logging
from dataclasses import asdict, dataclass
from uuid import uuid4

from django.forms.models import model_to_dict

from badgerdoc import temporal_client
from badgerdoc.models import document, extraction, task, workflow_registry

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocEvent:
    event_entity: str
    event_type: str
    document_type: str | None
    document_id: int
    supported_workflows: list[workflow_registry.WorkflowRegistry]
    task_id: int | None = None
    extraction_id: int | None = None


def trigger(
    event: BadgerdocEvent,
    workflow_type: str,
    task_queue: str,
) -> None:
    entity_id = event.document_id or event.task_id or event.extraction_id
    try:
        if not workflow_type or not task_queue:
            logger.warning(
                "Skipping workflow trigger - missing configuration: workflow_type=%s, task_queue=%s",
                workflow_type,
                task_queue,
            )
            return

        workflow_id = f"badgerdoc-lifecycle-{event.event_entity}-{event.event_type}-{entity_id}-{uuid4().hex[:5]}"

        event_dict = asdict(event)
        event_dict["supported_workflows"] = [
            {
                **model_to_dict(wf),
                "created_at": wf.created_at.isoformat(),
                "updated_at": wf.updated_at.isoformat(),
            }
            for wf in event.supported_workflows
        ]

        temporal_client.start_workflow(
            workflow_type=workflow_type,
            task_queue=task_queue,
            workflow_id=workflow_id,
            args=[event_dict],
        )

        logger.info(
            "Lifecycle workflow triggered successfully for %s %s %s. Workflow ID: %s",
            event.event_entity,
            entity_id,
            event.event_type,
            workflow_id,
        )

    except Exception:
        logger.exception(
            "Failed to trigger Lifecycle workflow for %s %s %s",
            getattr(event, "event_entity", "unknown"),
            getattr(event, "event_type", "unknown"),
            entity_id,
        )


@dataclass
class WorkflowParameters:
    event_entity: str | None
    event_type: str | None
    document_id: int
    scope: str | None = None
    workflow_registry_id: int | None = None
    task_id: int | None = None
    page_number: int | None = None
    extraction_id: int | None = None
    parameters: dict | None = None


def get_supported_workflows(
    params: WorkflowParameters,
    doc: document.Document,
    entity_tags: list[str] | None = None,
) -> list[workflow_registry.WorkflowRegistry]:
    document_types = [doc.extension] if doc.extension else None
    extraction_scope = [params.scope] if params.scope else None

    logger.info(
        "Searching for supported workflows with parameters: event_entity=%s, event_type=%s, document_types=%s, entity_tags=%s, extraction_scope=%s, trigger=%s",
        params.event_entity,
        params.event_type,
        document_types,
        entity_tags,
        extraction_scope,
        "automatic",
    )

    registries = workflow_registry.get_registries(
        event_entity=params.event_entity,
        event_type=params.event_type,
        document_types=document_types,
        entity_tags=entity_tags,
        extraction_scope=extraction_scope,
        trigger="automatic",
    )

    logger.info("Found %d supported workflow(s)", len(registries))

    return registries


def get_supported_workflows_by_document(
    params: WorkflowParameters, doc: document.Document
) -> list[workflow_registry.WorkflowRegistry]:
    entity_tags = doc.tags if doc.tags else []
    return get_supported_workflows(params, doc, entity_tags)


def get_supported_workflows_by_extraction(
    params: WorkflowParameters,
    doc: document.Document,
    ext: extraction.Extraction,
) -> list[workflow_registry.WorkflowRegistry]:
    entity_tags = ext.tags if ext.tags else []
    return get_supported_workflows(params, doc, entity_tags)


def get_supported_workflows_by_task(
    params: WorkflowParameters, doc: document.Document, tsk: task.Task
) -> list[workflow_registry.WorkflowRegistry]:
    entity_tags = tsk.tags if tsk.tags else []
    return get_supported_workflows(params, doc, entity_tags)
