import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_ocr_mineru.activities import mineru_activity
from badgerdoc_ocr_mineru.workflow import BadgerdocOCRMinerUWorkflow

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_ocr_mineru"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_ocr_mineru",
            workflows=[
                BadgerdocOCRMinerUWorkflow,
            ],
            activities=[
                mineru_activity.mineru_ocr_activity,
                mineru_activity.convert_to_hocr,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
