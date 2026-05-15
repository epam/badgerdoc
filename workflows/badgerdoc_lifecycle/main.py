import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_common.activities import (
    document,
    extraction,
    task,
    workflow_registry,
)
from badgerdoc_common.activities.agent_log import write_agent_log
from badgerdoc_lifecycle import (
    document_lifecycle,
    document_trigger,
    document_upload_example,
    extraction_example,
    manual_trigger_example,
)
from badgerdoc_lifecycle.activities import hocr_extraction

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_lifecycle"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_lifecycle",
            workflows=[
                document_lifecycle.BadgerdocLifecycleWorkflow,
                document_trigger.DocumentTriggerWorkflow,
                document_upload_example.BadgerdocDocumentUploadExampleWorkflow,
                extraction_example.BadgerdocExtractionExample,
                manual_trigger_example.ManualTriggerExampleWorkflow,
            ],
            activities=[
                write_agent_log,
                workflow_registry.badgerdoc_get_workflow_by_id,
                document.badgerdoc_get_document,
                document.badgerdoc_list_documents,
                task.badgerdoc_create_task,
                task.badgerdoc_get_task,
                document_upload_example.upload_example,
                extraction.badgerdoc_create_extraction,
                extraction.badgerdoc_create_extraction_page,
                extraction.badgerdoc_finish_extraction,
                extraction.badgerdoc_get_extraction,
                extraction.badgerdoc_get_latest_extraction_page,
                hocr_extraction.create_extraction_page,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
