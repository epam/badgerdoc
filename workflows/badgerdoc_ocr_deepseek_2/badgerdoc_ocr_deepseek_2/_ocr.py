import asyncio
import logging
from typing import Any

from temporalio import workflow

from badgerdoc_common import helpers, trigger
from badgerdoc_common.badgerdoc_ocr import BadgerdocOCRBase, OCRPageRequest
from badgerdoc_common.hocr import (
    BadgerdocHOCRPageResult,
    BadgerdocOCRPageResult,
)
from badgerdoc_ocr_deepseek_2.activities.ocr_convertors import (
    deepseek_ocr_2_results_to_hocr,
)
from badgerdoc_ocr_deepseek_2.activities.ocr_requests import (
    MAX_TOKENS,
    MODEL,
    PORT,
    PROMPT,
    deepseek_prepare_page,
    deepseek_store_result,
)

logger = logging.getLogger(__name__)


class Deepseek2OCR(BadgerdocOCRBase):

    def __init__(self) -> None:
        self._path_to_context: dict[str, tuple[int, dict]] = {}

    async def _ocr_one(
        self,
        extraction_id: int,
        extraction_tags: list[str],
        workflow_type: str,
        page_num: int,
        doc: Any,
        block_index: int | None = None,
    ) -> dict[str, Any]:
        prepare = await workflow.execute_activity(
            deepseek_prepare_page,
            args=[extraction_id, extraction_tags, page_num, doc],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        text: str = await workflow.execute_activity(
            "do_mlx_ocr",
            args=[prepare["image_url"], PORT, MODEL, PROMPT, MAX_TOKENS],
            task_queue="badgerdoc_mlx",
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
        )
        return await workflow.execute_activity(
            deepseek_store_result,
            args=[
                workflow_type,
                page_num,
                text,
                prepare["metadata"],
                block_index,
            ],
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

    async def ocr_pages(
        self,
        params: trigger.DocumentTriggerParams,
        pages: list[OCRPageRequest],
    ) -> list[BadgerdocOCRPageResult]:
        logger.info(
            "Deepseek2OCR.ocr_pages: starting OCR on %d page(s)", len(pages)
        )
        extraction_id = params.target_extraction.id
        extraction_tags = params.target_extraction.tags or []
        workflow_type = params.workflow.temporal_workflow_type

        raw_results: list[dict] = (
            list(
                await asyncio.gather(
                    *[
                        self._ocr_one(
                            extraction_id,
                            extraction_tags,
                            workflow_type,
                            req.badgerdoc_document.page_num,
                            req.badgerdoc_document.document,
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
            "Deepseek2OCR.ocr_pages: %d page(s) OCR complete", len(ocr_results)
        )
        return ocr_results

    async def ocr_blocks(
        self,
        params: trigger.DocumentTriggerParams,
        blocks: list[OCRPageRequest],
    ) -> list[BadgerdocOCRPageResult]:
        logger.info(
            "Deepseek2OCR.ocr_blocks: starting OCR on %d block(s)", len(blocks)
        )
        extraction_id = params.target_extraction.id
        extraction_tags = params.target_extraction.tags or []
        workflow_type = params.workflow.temporal_workflow_type

        raw_results: list[dict | BaseException] = (
            list(
                await asyncio.gather(
                    *[
                        self._ocr_one(
                            extraction_id,
                            extraction_tags,
                            workflow_type,
                            req.badgerdoc_document.page_num,
                            req.badgerdoc_document.document,
                            i,
                        )
                        for i, req in enumerate(blocks)
                    ],
                    return_exceptions=True,
                )
            )
            if blocks
            else []
        )

        ocr_results: list[BadgerdocOCRPageResult] = []
        for i, (req, result) in enumerate(zip(blocks, raw_results)):
            if isinstance(result, BaseException):
                logger.error(
                    "Deepseek2OCR.ocr_blocks: block %d (page %d) failed, inserting empty result",
                    i,
                    req.badgerdoc_document.page_num,
                    exc_info=result,
                )
                ocr_results.append(BadgerdocOCRPageResult(ocr={}))
                continue
            path = result["middle_json"]
            self._path_to_context[path] = (result["page_num"], result)
            ocr_results.append(
                BadgerdocOCRPageResult(ocr={str(result["page_num"]): [path]})
            )
            logger.info(
                "Deepseek2OCR.ocr_blocks: block %d (page %d) succeeded",
                i,
                req.badgerdoc_document.page_num,
            )

        failures = sum(1 for r in ocr_results if not r.ocr)
        logger.info(
            "Deepseek2OCR.ocr_blocks: %d block result(s) produced, %d failure(s)",
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
            "Deepseek2OCR.ocr_merge_blocks: %d page(s) after merge",
            len(merged),
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
            "Deepseek2OCR.convert_to_hocr: converting %d page(s) to hOCR",
            len(page_to_infos),
        )

        hocr_results: list[BadgerdocHOCRPageResult] = list(
            await asyncio.gather(
                *[
                    workflow.execute_activity(
                        deepseek_ocr_2_results_to_hocr,
                        args=[workflow_type, page_num, infos],
                        start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                        retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                    )
                    for page_num, infos in sorted(page_to_infos.items())
                ]
            )
        )

        logger.info(
            "Deepseek2OCR.convert_to_hocr: %d hOCR result(s) produced",
            len(hocr_results),
        )
        return hocr_results
