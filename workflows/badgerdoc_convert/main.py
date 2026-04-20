import asyncio

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_common.activities import document
from badgerdoc_convert import converters
from badgerdoc_convert.activities import dzi, pdf

helpers.configure_logging()


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration("badgerdoc_convert")
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_convert",
            workflows=[
                converters.BadgerdocPNGConvertWorkflow,
                converters.BadgerdocDZIConvertWorkflow,
            ],
            activities=[
                pdf.download_and_convert_document,
                dzi.convert_to_dzi,
                document.badgerdoc_get_document,
            ],
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
