import logging

from temporalio import workflow

from badgerdoc_common import trigger
from badgerdoc_common.badgerdoc_ocr import trigger_params_to_ocr_page
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_mineru._ocr import MinerUOCR

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocOCRMinerUWorkflow:

    @workflow.run
    async def run(
        self, params: trigger.DocumentTriggerParams
    ) -> BadgerdocHOCRPageResult:
        logger.info("BadgerdocOCRMinerUWorkflow: starting")

        ocr_container = await trigger_params_to_ocr_page(params)
        logger.info(
            "BadgerdocOCRMinerUWorkflow: OCR container resolved — %d page(s), %d block(s)",
            len(ocr_container.pages),
            len(ocr_container.blocks),
        )

        hocr_results = await MinerUOCR().run(params, ocr_container)

        combined: dict = {}
        for result in hocr_results:
            combined.update(result.h_ocr)

        logger.info(
            "BadgerdocOCRMinerUWorkflow: completed with %d hOCR entries",
            len(combined),
        )
        return BadgerdocHOCRPageResult(h_ocr=combined)
