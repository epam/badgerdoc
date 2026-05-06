import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_ocr_arbitrator import workflow
from badgerdoc_ocr_arbitrator import activities

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration(
        "badgerdoc_ocr_arbitrator"
    )
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_ocr_arbitrator",
            workflows=[workflow.BadgerdocOCRArbitratorWorkflow],
            activities=[
                activities.arbitrator.start_arbitrator,
                activities.wait.wait_for_triggered_workflows,
                activities.ocr.trial_process,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
