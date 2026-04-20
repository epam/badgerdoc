import logging
import os
from datetime import timedelta

from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

logger = logging.getLogger(__name__)

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT = timedelta(
    int(os.environ.get("BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT", 30))
)


def retry_policy_build(policy_string: str) -> RetryPolicy:
    values = policy_string.split(",")
    initial_interval = float(values[0])
    backoff_coefficient = float(values[1])
    maximum_interval = float(values[2])
    maximum_attempts = int(values[3])

    return RetryPolicy(
        initial_interval=timedelta(seconds=initial_interval),
        backoff_coefficient=backoff_coefficient,
        maximum_interval=timedelta(seconds=maximum_interval),
        maximum_attempts=maximum_attempts,
    )


def _get_badgerdoc_retry_policy() -> RetryPolicy:
    policy_string = os.getenv("BADGERDOC_REST_API_RETRY_POLICY")
    if not policy_string:
        raise ValueError(
            "BADGERDOC_REST_API_RETRY_POLICY environment variable is required"
        )
    return retry_policy_build(policy_string)


BadgerdocRestAPIRetryPolicy = _get_badgerdoc_retry_policy()


def configure_logging():
    logging.basicConfig(level=logging.INFO)


async def connect_to_client():
    logger.info(f"Connecting to Temporal client at %s", TEMPORAL_ADDRESS)
    client = await Client.connect(TEMPORAL_ADDRESS)
    logger.info("Connected")
    return client


async def start_worker(worker: Worker) -> None:
    logger.info("Starting new worker %s", worker)
    await worker.run()
