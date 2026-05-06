import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_common.activities.document import (
    badgerdoc_get_document_chunk,
    badgerdoc_get_rendition,
    badgerdoc_list_documents,
)
from badgerdoc_ocr_mineru.activities.ocr_convertors import (
    mineru_mlx_results_to_hocr,
)
from badgerdoc_ocr_mineru.activities.ocr_requests import (
    mineru_mlx_merge_and_store,
    mineru_mlx_ocr_page,
    mineru_mlx_tag_extraction,
)
from badgerdoc_ocr_mineru.workflow import BadgerdocOCRMinerUWorkflow

helpers.configure_logging()


async def worker() -> None:
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_ocr_mineru"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_ocr_mineru",
            workflows=[BadgerdocOCRMinerUWorkflow],
            activities=[
                mineru_mlx_tag_extraction,
                mineru_mlx_ocr_page,
                mineru_mlx_merge_and_store,
                mineru_mlx_results_to_hocr,
                badgerdoc_list_documents,
                badgerdoc_get_rendition,
                badgerdoc_get_document_chunk,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
