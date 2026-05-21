import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_common.activities.document import (
    badgerdoc_get_document_chunk,
    badgerdoc_get_rendition,
    badgerdoc_list_documents,
)
from badgerdoc_ocr_paddle import activities, workflow

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_ocr_paddle"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_ocr_paddle",
            workflows=[workflow.BadgerdocOCRPaddleWorkflow],
            activities=[
                activities.ocr_requests.paddle_ocr_tag_extraction,
                activities.ocr_requests.paddle_prepare_page,
                activities.ocr_requests.paddle_store_result,
                activities.ocr_convertors.paddle_ocr_results_to_hocr,
                badgerdoc_list_documents,
                badgerdoc_get_rendition,
                badgerdoc_get_document_chunk,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
