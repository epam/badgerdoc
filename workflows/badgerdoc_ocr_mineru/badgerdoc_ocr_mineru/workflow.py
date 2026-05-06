import asyncio
import logging

from temporalio import workflow

from badgerdoc_common import helpers, trigger
from badgerdoc_common.badgerdoc_ocr import trigger_params_to_ocr_page
from badgerdoc_common.hocr import BadgerdocHOCRPageResult
from badgerdoc_ocr_mineru.activities.ocr_convertors import (
    mineru_mlx_results_to_hocr,
)
from badgerdoc_ocr_mineru.activities.ocr_requests import (
    mineru_mlx_merge_and_store,
    mineru_mlx_ocr_page,
)

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
            "BadgerdocOCRMinerUWorkflow: OCR container resolved — %d pages, %d blocks",
            len(ocr_container.pages),
            len(ocr_container.blocks),
        )

        extraction_id = params.target_extraction.id
        extraction_tags = params.target_extraction.tags or []
        workflow_type = params.workflow.temporal_workflow_type

        # Step 1: OCR all full pages in parallel
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 1 — OCR %d page(s)",
            len(ocr_container.pages),
        )
        page_ocr_results: list[dict] = (
            list(
                await asyncio.gather(
                    *[
                        workflow.execute_activity(
                            mineru_mlx_ocr_page,
                            args=[
                                extraction_id,
                                extraction_tags,
                                workflow_type,
                                req.badgerdoc_document.page_num,
                                req.badgerdoc_document.document,
                            ],
                            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                        )
                        for req in ocr_container.pages
                    ]
                )
            )
            if ocr_container.pages
            else []
        )

        # Step 2: OCR all blocks sequentially (continue on individual failure)
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 2 — OCR %d block(s)",
            len(ocr_container.blocks),
        )
        block_ocr_results: list[dict] = []
        for i, req in enumerate(ocr_container.blocks):
            try:
                result = await workflow.execute_activity(
                    mineru_mlx_ocr_page,
                    args=[
                        extraction_id,
                        extraction_tags,
                        workflow_type,
                        req.badgerdoc_document.page_num,
                        req.badgerdoc_document.document,
                        i,
                    ],
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
                block_ocr_results.append(result)
                logger.info(
                    "BadgerdocOCRMinerUWorkflow: block %d (page %d) succeeded",
                    i,
                    req.badgerdoc_document.page_num,
                )
            except Exception:  # pylint: disable=broad-except
                logger.exception(
                    "BadgerdocOCRMinerUWorkflow: block %d (page %d) failed, skipping",
                    i,
                    req.badgerdoc_document.page_num,
                )

        # Step 3: Merge all OCR results and store one manifest per page in MinIO
        all_ocr_results = page_ocr_results + block_ocr_results
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 3 — merge %d OCR result(s)",
            len(all_ocr_results),
        )
        page_manifest_paths: dict[str, str] = await workflow.execute_activity(
            mineru_mlx_merge_and_store,
            args=[workflow_type, all_ocr_results],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        # Step 4: Convert each page's OCR to hOCR in parallel
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 4 — convert %d page(s) to hOCR",
            len(page_manifest_paths),
        )
        hocr_results: list[BadgerdocHOCRPageResult] = list(
            await asyncio.gather(
                *[
                    workflow.execute_activity(
                        mineru_mlx_results_to_hocr,
                        args=[
                            workflow_type,
                            int(page_num),
                            page_manifest_path,
                        ],
                        start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                        retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                    )
                    for page_num, page_manifest_path in sorted(
                        page_manifest_paths.items(), key=lambda x: int(x[0])
                    )
                ]
            )
        )

        combined: dict = {}
        for result in hocr_results:
            combined.update(result.h_ocr)

        logger.info(
            "BadgerdocOCRMinerUWorkflow: completed with %d hOCR entries",
            len(combined),
        )
        return BadgerdocHOCRPageResult(h_ocr=combined)
