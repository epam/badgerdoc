import logging

from temporalio import workflow

from badgerdoc_common import trigger
from badgerdoc_common.badgerdoc_ocr import trigger_params_to_ocr_page
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_paddle._ocr import PaddleOCR

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocOCRPaddleWorkflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("BadgerdocOCRPaddleWorkflow: starting")

        ocr_container = await trigger_params_to_ocr_page(params)
        logger.info(
            "BadgerdocOCRPaddleWorkflow: OCR container resolved — %d page(s), %d block(s)",
            len(ocr_container.pages),
            len(ocr_container.blocks),
        )

        hocr_results = await PaddleOCR().run(params, ocr_container)

        combined: dict = {}
        for result in hocr_results:
            combined.update(result.h_ocr)

        logger.info(
            "BadgerdocOCRPaddleWorkflow: completed with %d hOCR entries",
            len(combined),
        )
        return BadgerdocHOCRPageResult(h_ocr=combined)
