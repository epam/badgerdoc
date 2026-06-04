import logging
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from badgerdoc_common import agent_logger
from badgerdoc_common.activities import document
from badgerdoc_common.badgerdoc_event import BadgerdocEvent
from badgerdoc_convert.activities import dzi, pdf

logger = logging.getLogger(__name__)

MAXIMUM_CONVERT_TIMEOUT_SECONDS = 900


class BadgerdocPNGConvertError(Exception):
    pass


@workflow.defn
class BadgerdocPNGConvertWorkflow:

    @workflow.run
    async def run(self, request_data: BadgerdocEvent) -> Any:
        logger.info("Starting BadgerDoc document preproccesing")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )
        document_id = request_data.document_id

        try:
            result = await workflow.execute_activity(
                pdf.download_and_convert_document,
                document_id,
                start_to_close_timeout=timedelta(
                    seconds=MAXIMUM_CONVERT_TIMEOUT_SECONDS
                ),
                retry_policy=retry_policy,
            )
        except Exception as e:
            raise BadgerdocPNGConvertError("Failed to process document") from e

        return result


@workflow.defn
class BadgerdocDZIConvertWorkflow:

    @workflow.run
    async def run(self, request_data: BadgerdocEvent) -> Any:
        log = agent_logger.get_logger(document_id=request_data.document_id)

        await log.info("Starting BadgerDoc PNG -> DZI convert")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )
        document_id = request_data.document_id
        current_document: document.BadgerdocDocument
        current_document = await workflow.execute_activity(
            document.badgerdoc_get_document,
            document_id,
            start_to_close_timeout=timedelta(
                seconds=MAXIMUM_CONVERT_TIMEOUT_SECONDS
            ),
            retry_policy=retry_policy,
        )
        logger.info("Got document: %s:", current_document)
        logger.info(
            "Checking if tag rendition present in tags: %s",
            current_document.tags,
        )

        if (
            not current_document.tags
            or "rendition" not in current_document.tags
        ):
            logger.info("Not renditions convert is not supported by workflow")
            return
        if current_document.parent_document_id is None:
            logger.info("No parent_document_id detected, can't convet to DZI")
            return

        logger.info("Converting...")
        conversion_result = await workflow.execute_activity(
            dzi.convert_to_dzi,
            current_document,
            start_to_close_timeout=timedelta(
                seconds=MAXIMUM_CONVERT_TIMEOUT_SECONDS
            ),
            retry_policy=retry_policy,
        )
        await log.info("BadgerDoc PNG -> DZI convert completed")
        return conversion_result
