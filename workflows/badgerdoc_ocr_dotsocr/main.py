import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_common.activities import document
from badgerdoc_ocr_dotsocr import dotsocr_workflow
from badgerdoc_ocr_dotsocr.activities import dotsocr_activity

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_ocr_dotsocr"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_ocr_dotsocr",
            workflows=[
                dotsocr_workflow.BadgerdocOCRDotsOCRWorkflow,
            ],
            activities=[
                dotsocr_activity.dots_ocr_activity,
                dotsocr_activity.convert_to_hocr,
                document.badgerdoc_get_document,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
