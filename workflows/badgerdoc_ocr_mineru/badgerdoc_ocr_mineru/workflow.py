import logging

from temporalio import workflow

from badgerdoc_common import helpers, trigger
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_mineru.activities import mineru_activity

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocOCRMinerUWorkflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("Starting BadgerdocOCRMinerUWorkflow")
        logger.info("Received params: %s", params)

        result = await workflow.execute_activity(
            mineru_activity.mineru_ocr_activity,
            params,
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        hocr_path = await workflow.execute_activity(
            mineru_activity.convert_to_hocr,
            args=[params, result],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        # Save hOCR to the Badgerdoc page

        logger.info("hOCR file created at: %s", hocr_path)

        logger.info("BadgerdocOCRMinerUWorkflow completed")

        return hocr_path
