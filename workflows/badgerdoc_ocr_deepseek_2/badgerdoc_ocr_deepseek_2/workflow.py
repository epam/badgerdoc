import logging

from temporalio import workflow

from badgerdoc_common import trigger
from badgerdoc_common.badgerdoc_ocr import trigger_params_to_ocr_page
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_deepseek_2._ocr import Deepseek2OCR

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocDeepseek2Workflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("BadgerdocDeepseek2Workflow: starting")

        ocr_container = await trigger_params_to_ocr_page(params)
        logger.info(
            "BadgerdocDeepseek2Workflow: OCR container resolved — %d page(s), %d block(s)",
            len(ocr_container.pages),
            len(ocr_container.blocks),
        )

        hocr_results = await Deepseek2OCR().run(params, ocr_container)

        combined: dict = {}
        for result in hocr_results:
            combined.update(result.h_ocr)

        logger.info(
            "BadgerdocDeepseek2Workflow: completed with %d hOCR entries",
            len(combined),
        )
        return BadgerdocHOCRPageResult(h_ocr=combined)
