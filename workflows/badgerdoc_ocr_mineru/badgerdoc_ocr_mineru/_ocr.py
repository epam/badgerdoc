import asyncio
import logging

from temporalio import workflow

from badgerdoc_common import helpers, trigger
from badgerdoc_common.badgerdoc_ocr import BadgerdocOCRBase, OCRPageRequest
from badgerdoc_common.hocr import (
    BadgerdocHOCRPageResult,
    BadgerdocOCRPageResult,
)
from badgerdoc_ocr_mineru.activities.ocr_convertors import (
    mineru_mlx_results_to_hocr,
)
from badgerdoc_ocr_mineru.activities.ocr_requests import (
    mineru_mlx_ocr_page,
    mineru_mlx_tag_extraction,
)

logger = logging.getLogger(__name__)


class MinerUOCR(BadgerdocOCRBase):

    def __init__(self) -> None:
        self._path_to_context: dict[str, tuple[int, dict]] = {}

    async def run(
        self,
        params: trigger.DocumentTriggerParams,
        ocr_container,
    ) -> list[BadgerdocHOCRPageResult]:
        # Tag the extraction once before any OCR activity runs.
        await workflow.execute_activity(
            mineru_mlx_tag_extraction,
            args=[
                params.target_extraction.id,
                params.target_extraction.tags or [],
            ],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        return await super().run(params, ocr_container)

    async def ocr_pages(
        self,
        params: trigger.DocumentTriggerParams,
        pages: list[OCRPageRequest],
    ) -> list[BadgerdocOCRPageResult]:
        logger.info(
            "MinerUOCR.ocr_pages: starting OCR on %d page(s)", len(pages)
        )
        workflow_type = params.workflow.temporal_workflow_type

        raw_results: list[dict] = (
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
                        for req in pages
                    ]
                )
            )
            if pages
            else []
        )

        ocr_results: list[BadgerdocOCRPageResult] = []
        for result in raw_results:
            path = result["middle_json"]
            self._path_to_context[path] = (result["page_num"], result)
            ocr_results.append(
                BadgerdocOCRPageResult(ocr={str(result["page_num"]): [path]})
            )

        logger.info(
            "MinerUOCR.ocr_pages: %d page(s) OCR complete", len(ocr_results)
        )
        return ocr_results

    async def ocr_blocks(
        self,
        params: trigger.DocumentTriggerParams,
        blocks: list[OCRPageRequest],
    ) -> list[BadgerdocOCRPageResult]:
        logger.info(
            "MinerUOCR.ocr_blocks: starting OCR on %d block(s)", len(blocks)
        )
        workflow_type = params.workflow.temporal_workflow_type

        raw_block_results = (
            await asyncio.gather(
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
                    for i, req in enumerate(blocks)
                ],
                return_exceptions=True,
            )
            if blocks
            else []
        )

        ocr_results: list[BadgerdocOCRPageResult] = []
        for i, result in enumerate(raw_block_results):
            if isinstance(result, BaseException):
                logger.exception(
                    "MinerUOCR.ocr_blocks: block %d failed, inserting empty result: %s",
                    i,
                    result,
                )
                ocr_results.append(BadgerdocOCRPageResult(ocr={}))
            else:
                path = result["middle_json"]
                self._path_to_context[path] = (result["page_num"], result)
                ocr_results.append(
                    BadgerdocOCRPageResult(
                        ocr={str(result["page_num"]): [path]}
                    )
                )
                logger.info(
                    "MinerUOCR.ocr_blocks: block %d (page %d) succeeded",
                    i,
                    result["page_num"],
                )

        failures = sum(1 for r in ocr_results if not r.ocr)
        logger.info(
            "MinerUOCR.ocr_blocks: %d block result(s) produced, %d failure(s)",
            len(ocr_results),
            failures,
        )
        return ocr_results

    async def align_coordinates(
        self,
        params: trigger.DocumentTriggerParams,  # pylint: disable=unused-argument
        block: OCRPageRequest,  # pylint: disable=unused-argument
        result: BadgerdocOCRPageResult,
    ) -> BadgerdocOCRPageResult:
        # Pass-through: coordinate remapping is handled inside mineru_mlx_results_to_hocr
        # using metadata.position_in_parent for each info dict.
        return result

    async def ocr_merge_blocks(
        self,
        pages: list[BadgerdocOCRPageResult],
        blocks: list[BadgerdocOCRPageResult],
    ) -> list[BadgerdocOCRPageResult]:
        merged: dict[str, list[str]] = {}
        for r in pages + blocks:
            for page_num, paths in r.ocr.items():
                merged.setdefault(page_num, []).extend(paths)
        logger.info(
            "MinerUOCR.ocr_merge_blocks: %d page(s) after merge", len(merged)
        )
        return [BadgerdocOCRPageResult(ocr=merged)]

    async def convert_to_hocr(
        self,
        params: trigger.DocumentTriggerParams,
        results: list[BadgerdocOCRPageResult],
    ) -> list[BadgerdocHOCRPageResult]:
        workflow_type = params.workflow.temporal_workflow_type

        page_to_infos: dict[int, list[dict]] = {}
        for result in results:
            for _, paths in result.ocr.items():
                for path in paths:
                    page_num, info = self._path_to_context[path]
                    page_to_infos.setdefault(page_num, []).append(info)

        logger.info(
            "MinerUOCR.convert_to_hocr: converting %d page(s) to hOCR",
            len(page_to_infos),
        )

        hocr_results: list[BadgerdocHOCRPageResult] = list(
            await asyncio.gather(
                *[
                    workflow.execute_activity(
                        mineru_mlx_results_to_hocr,
                        args=[workflow_type, page_num, infos],
                        start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                        retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                    )
                    for page_num, infos in sorted(page_to_infos.items())
                ]
            )
        )

        logger.info(
            "MinerUOCR.convert_to_hocr: %d hOCR result(s) produced",
            len(hocr_results),
        )
        return hocr_results
