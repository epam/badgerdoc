import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_ocr_dial import activities, workflow

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_ocr_dial"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_ocr_dial",
            workflows=[workflow.BadgerdocOCRDialWorkflow],
            activities=[
                activities.ocr.trial_process,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
