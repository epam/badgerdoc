import asyncio
import os

from temporalio.worker import Worker

from badgerdoc_common import helpers, sentry
from badgerdoc_mlx.activities.ocr_requests import do_mlx_ocr, do_mlx_ocr_mineru

helpers.configure_logging()

# Fan-in concurrency limit: controls how many MLX requests run in parallel.
# All other requests queue in Temporal until a slot is free.
_MAX_CONCURRENCY = int(os.getenv("MLX_WORKER_MAX_CONCURRENCY", "1"))


async def worker():
    client = await helpers.connect_to_client()
    sentry_config = sentry.get_sentry_worker_configuration("badgerdoc_mlx")
    await helpers.start_worker(
        Worker(
            client,
            task_queue="badgerdoc_mlx",
            workflows=[],
            activities=[do_mlx_ocr, do_mlx_ocr_mineru],
            max_concurrent_activities=_MAX_CONCURRENCY,
            **sentry_config,
        )
    )


if __name__ == "__main__":
    asyncio.run(worker())
