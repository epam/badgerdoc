import logging
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from badgerdoc_common import helpers, hocr, trigger
    from badgerdoc_ocr_dotsocr.activities import dotsocr_activity

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocOCRDotsOCRWorkflow:

    @workflow.run
    async def run(
        self, trigger_params: trigger.DocumentTriggerParams
    ) -> hocr.BadgerdocHOCRPageResult:
        result = await workflow.execute_activity(
            dotsocr_activity.dots_ocr_activity,
            trigger_params,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        return await workflow.execute_activity(
            dotsocr_activity.convert_to_hocr,
            args=[trigger_params, result["json_path"]],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
