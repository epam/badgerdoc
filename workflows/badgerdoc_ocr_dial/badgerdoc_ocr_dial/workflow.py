import logging

from temporalio import workflow

from badgerdoc_common import helpers, trigger
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_dial.activities.ocr import trial_process

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocOCRDialWorkflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("Starting BadgerdocOCRDialWorkflow")
        logger.info("Received params: %s", params)

        result = await workflow.execute_activity(
            trial_process,
            params,
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        logger.info("OCR processing completed")
        return result
