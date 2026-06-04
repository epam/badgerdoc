import logging
from datetime import timedelta

from temporalio import workflow

from badgerdoc_common import agent_logger, helpers, trigger
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_arbitrator.activities import arbitrator, ocr, wait

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocOCRArbitratorWorkflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("Starting BadgerdocOCRArbitratorWorkflow")
        logger.info("Received params: %s", params)
        log = agent_logger.get_logger(
            document_id=params.original_document.id,
            task_id=params.original_task.id if params.original_task else None,
        )
        await log.info("Starting OCR Arbitrator")

        workflow_results = await workflow.execute_activity(
            arbitrator.start_arbitrator,
            params,
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        await log.info("Waiting for all agents to be completed")
        workflow_results = await workflow.execute_activity(
            wait.wait_for_triggered_workflows,
            args=[workflow_results],
            start_to_close_timeout=timedelta(hours=2),
            heartbeat_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        await log.info("All agents completed. Starting arbitration.")
        result = await workflow.execute_activity(
            ocr.trial_process,
            args=[params, workflow_results],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        await log.info("Arbitration completed")

        return result
