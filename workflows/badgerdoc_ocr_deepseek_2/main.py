import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_ocr_deepseek_2 import activities, workflow

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_ocr_deepseek_2"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_ocr_deepseek_2",
            workflows=[workflow.BadgerdocDeepseek2Workflow],
            activities=[
                activities.ocr_requests.deepseek_ocr_2,
                activities.ocr_convertors.deepseek_ocr_2_results_to_hocr,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
