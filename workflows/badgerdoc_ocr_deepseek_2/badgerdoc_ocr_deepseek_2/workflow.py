import asyncio
import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

from badgerdoc_common import trigger
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_deepseek_2.activities.ocr_convertors import (
    deepseek_ocr_2_results_to_hocr,
)
from badgerdoc_ocr_deepseek_2.activities.ocr_requests import deepseek_ocr_2

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocDeepseek2Workflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("Starting BadgerDoc document OCR proccesing.")

        if not params.linked_document_pages:
            raise ApplicationError(
                "linked_document_pages is required",
                type="InvalidScopePassed",
                non_retryable=True,
            )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )

        ocr_results = await asyncio.gather(
            *[
                workflow.execute_activity(
                    deepseek_ocr_2,
                    args=[params, page],
                    schedule_to_start_timeout=timedelta(seconds=600),
                    schedule_to_close_timeout=timedelta(seconds=600),
                    start_to_close_timeout=timedelta(seconds=600),
                    retry_policy=retry_policy,
                )
                for page in params.linked_document_pages
            ]
        )

        hocr_results = await asyncio.gather(
            *[
                workflow.execute_activity(
                    deepseek_ocr_2_results_to_hocr,
                    args=[params, page, result],
                    schedule_to_start_timeout=timedelta(seconds=60),
                    schedule_to_close_timeout=timedelta(seconds=60),
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy,
                )
                for page, result in zip(
                    params.linked_document_pages, ocr_results
                )
            ]
        )

        combined_hocr: dict = {}
        for result in hocr_results:
            combined_hocr.update(result.h_ocr)

        logger.info("BadgerdocDeepseek2Workflow completed")
        return BadgerdocHOCRPageResult(h_ocr=combined_hocr)
