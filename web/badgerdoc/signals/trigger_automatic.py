import logging
import os

from django.db.models.signals import post_save
from django.dispatch import receiver

from badgerdoc.models import document, extraction, task
from badgerdoc.signals import workflow

logger = logging.getLogger(__name__)


def _trigger_document_workflow(
    instance: document.Document,
    event_entity: str,
    event_type: str,
    supported_workflows: list,
) -> None:
    event = workflow.BadgerdocEvent(
        event_entity=event_entity,
        event_type=event_type,
        document_id=instance.pk,
        document_type=instance.extension,
        supported_workflows=supported_workflows,
    )

    workflow_type = os.getenv("BADGERDOC_LIFECYCLE_WORKFLOW_TYPE", "")
    task_queue = os.getenv("BADGERDOC_LIFECYCLE_QUEUE", "")
    if supported_workflows:
        workflow.trigger(
            event,
            workflow_type,
            task_queue,
        )
    else:
        logging.info("No workflows found to be triggered")


@receiver(post_save, sender=document.Document)
def handle_document_save(
    sender, instance: document.Document, created: bool, **kwargs
):  # pylint: disable=unused-argument

    if created:
        logger.info(
            "Document uploaded: %s by %s",
            instance.file.name,
            instance.uploaded_by,
        )
        params = workflow.WorkflowParameters(
            event_entity="document",
            event_type="on_create",
            document_id=instance.pk,
        )
        supported_workflows = workflow.get_supported_workflows_by_document(
            params, instance
        )
        _trigger_document_workflow(
            instance,
            "document",
            "on_create",
            supported_workflows,
        )
    else:
        logger.info("Document updated: %s", instance.file.name)
        params = workflow.WorkflowParameters(
            event_entity="document",
            event_type="on_update",
            document_id=instance.pk,
        )
        supported_workflows = workflow.get_supported_workflows_by_document(
            params, instance
        )
        _trigger_document_workflow(
            instance,
            "document",
            "on_update",
            supported_workflows,
        )


@receiver(post_save, sender=extraction.Extraction)
def handle_extraction_save(
    sender, instance: extraction.Extraction, created: bool, **kwargs
):  # pylint: disable=unused-argument

    if created:
        logger.info(
            "Extraction created: %s for document %s by %s",
            instance.pk,
            instance.document.pk,
            instance.created_by.username,
        )
        params = workflow.WorkflowParameters(
            event_entity="extraction",
            event_type="on_create",
            document_id=instance.document.pk,
        )
        supported_workflows = workflow.get_supported_workflows_by_extraction(
            params, instance.document, instance
        )
        _trigger_document_workflow(
            instance.document,
            "extraction",
            "on_create",
            supported_workflows,
        )
    else:
        logger.info("Extraction updated: %s", instance.pk)
        params = workflow.WorkflowParameters(
            event_entity="extraction",
            event_type="on_update",
            document_id=instance.document.pk,
        )
        supported_workflows = workflow.get_supported_workflows_by_extraction(
            params, instance.document, instance
        )
        _trigger_document_workflow(
            instance.document,
            "extraction",
            "on_update",
            supported_workflows,
        )


@receiver(post_save, sender=task.Task)
def handle_task_save(
    sender, instance: task.Task, created: bool, **kwargs
):  # pylint: disable=unused-argument

    if created:
        logger.info(
            "Task created: %s by %s",
            instance.pk,
            instance.user.username,
        )
        params = workflow.WorkflowParameters(
            event_entity="task",
            event_type="on_create",
            document_id=instance.document.pk,
        )
        supported_workflows = workflow.get_supported_workflows_by_task(
            params, instance.document, instance
        )
        _trigger_document_workflow(
            instance.document,
            "task",
            "on_create",
            supported_workflows,
        )
    else:
        logger.info("Task updated: %s", instance.pk)
        params = workflow.WorkflowParameters(
            event_entity="task",
            event_type="on_update",
            document_id=instance.document.pk,
        )
        supported_workflows = workflow.get_supported_workflows_by_task(
            params, instance.document, instance
        )
        _trigger_document_workflow(
            instance.document,
            "task",
            "on_update",
            supported_workflows,
        )
