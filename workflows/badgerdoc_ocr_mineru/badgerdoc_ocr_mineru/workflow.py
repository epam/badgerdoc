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
    mineru_mlx_tag_extraction,
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

        # Step 1: Tag the extraction once before any fan-out
        await workflow.execute_activity(
            mineru_mlx_tag_extraction,
            args=[extraction_id, extraction_tags],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        # Step 2: OCR all full pages in parallel
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 2 — OCR %d page(s)",
            len(ocr_container.pages),
        )
        page_ocr_results: list[dict] = (
            list(
                await asyncio.gather(
                    *[
                        workflow.execute_activity(
                            mineru_mlx_ocr_page,
                            args=[
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

        # Step 3: OCR all blocks in parallel (continue on individual failure)
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 3 — OCR %d block(s)",
            len(ocr_container.blocks),
        )
        raw_block_results = await asyncio.gather(
            *[
                workflow.execute_activity(
                    mineru_mlx_ocr_page,
                    args=[
                        workflow_type,
                        req.badgerdoc_document.page_num,
                        req.badgerdoc_document.document,
                        i,
                    ],
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
                for i, req in enumerate(ocr_container.blocks)
            ],
            return_exceptions=True,
        ) if ocr_container.blocks else []
        block_ocr_results: list[dict] = []
        for i, result in enumerate(raw_block_results):
            if isinstance(result, BaseException):
                logger.exception(
                    "BadgerdocOCRMinerUWorkflow: block %d failed, skipping: %s",
                    i,
                    result,
                )
            else:
                block_ocr_results.append(result)

        # Step 4: Merge all OCR results and store one manifest per page in MinIO
        all_ocr_results = page_ocr_results + block_ocr_results
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 4 — merge %d OCR result(s)",
            len(all_ocr_results),
        )
        page_manifest_paths: dict[str, str] = await workflow.execute_activity(
            mineru_mlx_merge_and_store,
            args=[workflow_type, all_ocr_results],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        # Step 5: Convert each page's OCR to hOCR in parallel
        logger.info(
            "BadgerdocOCRMinerUWorkflow: step 5 — convert %d page(s) to hOCR",
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
