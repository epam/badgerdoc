import logging
from datetime import timedelta

from temporalio import workflow

from badgerdoc_common import helpers, trigger
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_arbitrator.activities import ocr, arbitrator, wait

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocOCRArbitratorWorkflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("Starting BadgerdocOCRArbitratorWorkflow")
        logger.info("Received params: %s", params)

        workflow_results = await workflow.execute_activity(
            arbitrator.start_arbitrator,
            params,
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        workflow_results = await workflow.execute_activity(
            wait.wait_for_triggered_workflows,
            args=[workflow_results],
            start_to_close_timeout=timedelta(hours=2),
            heartbeat_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        result = await workflow.execute_activity(
            ocr.trial_process,
            args=[params, workflow_results],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        logger.info("OCR processing completed")

        return result
