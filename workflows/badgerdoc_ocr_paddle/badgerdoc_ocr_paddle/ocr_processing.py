import logging
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from badgerdoc_common import trigger
from badgerdoc_ocr_paddle.activities.ocr_convertors import (
    paddle_ocr_results_to_hocr,
)
from badgerdoc_ocr_paddle.activities.ocr_requests import paddle_ocr

logger = logging.getLogger(__name__)


class BadgerdocOCRError(Exception):
    pass


@workflow.defn
class BadgerdocOCRPaddleWorkflow:

    @workflow.run
    async def run(self, params: trigger.DocumentTriggerParams) -> Any:
        logger.info("Starting BadgerDoc document OCR proccesing.")
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )

        logger.info("Start OCR...")

        try:
            ocr_result_info = await workflow.execute_activity(
                paddle_ocr,
                params,
                schedule_to_start_timeout=timedelta(seconds=600),
                schedule_to_close_timeout=timedelta(seconds=600),
                start_to_close_timeout=timedelta(seconds=600),
                retry_policy=retry_policy,
            )
        except Exception as e:
            logger.warning("Activity ocr_request failed: %s", str(e))
            raise BadgerdocOCRError("Failed to start OCR") from e

        try:
            converted_ocr_results = await workflow.execute_activity(
                paddle_ocr_results_to_hocr,
                args=[params, ocr_result_info],
                schedule_to_start_timeout=timedelta(seconds=60),
                schedule_to_close_timeout=timedelta(seconds=60),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            )
        except Exception as e:
            logger.warning("Activity ocr_convertor failed: %s", str(e))
            raise BadgerdocOCRError("Failed to convert OCR results") from e

        return converted_ocr_results
