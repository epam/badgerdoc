import asyncio
import logging
from typing import Any

from temporalio import workflow

from badgerdoc_common import helpers, hocr, trigger
from badgerdoc_common.badgerdoc_ocr import BadgerdocOCRBase, OCRPageRequest
from badgerdoc_ocr_deepseek_2.activities.ocr_convertors import (
    deepseek_ocr_2_results_to_hocr,
)
from badgerdoc_ocr_deepseek_2.activities.ocr_requests import (
    deepseek_ocr_from_page,
)

logger = logging.getLogger(__name__)


class Deepseek2OCR(BadgerdocOCRBase):
    """DeepSeek OCR-2 implementation of BadgerdocOCRBase.

    Uses the mlx_vlm.server (OpenAI-compatible) inference endpoint backed by
    mlx-community/DeepSeek-OCR-2-bf16 to convert page/block images to text,
    then parses DeepSeek's <|ref|>...<|det|> tagged output into hOCR.

    Activity args use only primitives or single-level dataclasses (BadgerdocDocument).
    Temporal's default JSON converter reconstructs single-level dataclasses correctly
    but silently falls back to plain dict for multi-level nesting (e.g.
    BadgerdocDocumentPage.document or DocumentTriggerParams.linked_document_pages).
    """

    def __init__(self) -> None:
        # Maps middle_json storage path → (page_num, raw activity result dict)
        # so convert_to_hocr can look up context for every path.
        self._path_to_context: dict[str, tuple[int, dict[str, Any]]] = {}

    async def ocr_pages(
        self,
        params: trigger.DocumentTriggerParams,
        pages: list[OCRPageRequest],
    ) -> list[hocr.BadgerdocOCRPageResult]:
        logger.info("ocr_pages: starting, %d pages to process", len(pages))
        if not pages:
            logger.info("ocr_pages: no pages, returning empty")
            return []

        extraction_id = params.target_extraction.id
        extraction_tags = params.target_extraction.tags or []
        workflow_type = params.workflow.temporal_workflow_type

        infos: list[dict[str, Any]] = await asyncio.gather(
            *[
                workflow.execute_activity(
                    deepseek_ocr_from_page,
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
                for req in pages
            ]
        )

        results: list[hocr.BadgerdocOCRPageResult] = []
        for req, info in zip(pages, infos):
            page_num = req.badgerdoc_document.page_num
            path: str = info["middle_json"]
            self._path_to_context[path] = (page_num, info)
            results.append(
                hocr.BadgerdocOCRPageResult(ocr={str(page_num): [path]})
            )

        logger.info("ocr_pages: completed, %d pages processed", len(results))
        return results

    async def ocr_blocks(
        self,
        params: trigger.DocumentTriggerParams,
        blocks: list[OCRPageRequest],
    ) -> list[hocr.BadgerdocOCRPageResult]:
        logger.info("ocr_blocks: starting, %d blocks to process", len(blocks))
        if not blocks:
            logger.info("ocr_blocks: no blocks, returning empty")
            return []

        extraction_id = params.target_extraction.id
        extraction_tags = params.target_extraction.tags or []
        workflow_type = params.workflow.temporal_workflow_type

        results: list[hocr.BadgerdocOCRPageResult] = []
        for i, req in enumerate(blocks):
            page_num = req.badgerdoc_document.page_num
            doc = req.badgerdoc_document.document
            try:
                info: dict[str, Any] = await workflow.execute_activity(
                    deepseek_ocr_from_page,
                    args=[
                        extraction_id,
                        extraction_tags,
                        workflow_type,
                        page_num,
                        doc,
                        i,
                    ],
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
                path = info["middle_json"]
                self._path_to_context[path] = (page_num, info)
                results.append(
                    hocr.BadgerdocOCRPageResult(ocr={str(page_num): [path]})
                )
                logger.info(
                    "ocr_blocks: block %d (page %d) processed", i, page_num
                )
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "ocr_blocks: block %d (page %d) failed, inserting empty result",
                    i,
                    page_num,
                )
                results.append(hocr.BadgerdocOCRPageResult(ocr={}))

        skipped = sum(1 for r in results if not r.ocr)
        logger.info(
            "ocr_blocks: completed — %d succeeded, %d failed",
            len(results) - skipped,
            skipped,
        )
        return results

    async def align_coordinates(
        self,
        _params: trigger.DocumentTriggerParams,
        _block: OCRPageRequest,
        result: hocr.BadgerdocOCRPageResult,
    ) -> hocr.BadgerdocOCRPageResult:
        # deepseek_ocr_2_results_to_hocr reads position_in_parent from the
        # block metadata and remaps coordinates internally, so no further
        # transformation is needed here.
        return result

    async def ocr_merge_blocks(
        self,
        pages: list[hocr.BadgerdocOCRPageResult],
        blocks: list[hocr.BadgerdocOCRPageResult],
    ) -> list[hocr.BadgerdocOCRPageResult]:
        logger.info(
            "ocr_merge_blocks: merging %d page results and %d block results",
            len(pages),
            len(blocks),
        )
        merged: dict[str, list[str]] = {}

        for page_result in pages:
            for page_num, paths in page_result.ocr.items():
                merged.setdefault(page_num, []).extend(paths)

        for block_result in blocks:
            for page_num, paths in block_result.ocr.items():
                merged.setdefault(page_num, []).extend(paths)

        logger.info(
            "ocr_merge_blocks: produced 1 merged result covering %d pages",
            len(merged),
        )
        return [hocr.BadgerdocOCRPageResult(ocr=merged)]

    async def convert_to_hocr(
        self,
        params: trigger.DocumentTriggerParams,
        results: list[hocr.BadgerdocOCRPageResult],
    ) -> list[hocr.BadgerdocHOCRPageResult]:
        total_paths = sum(
            len(paths) for r in results for paths in r.ocr.values()
        )
        logger.info(
            "convert_to_hocr: starting conversion of %d OCR paths across %d result sets",
            total_paths,
            len(results),
        )

        workflow_type = params.workflow.temporal_workflow_type

        # Group all infos by page_num so multiple blocks on the same page
        # are merged into a single hOCR file.
        page_to_infos: dict[int, list[dict[str, Any]]] = {}
        for result in results:
            for paths in result.ocr.values():
                for path in paths:
                    context = self._path_to_context.get(path)
                    if context is None:
                        logger.warning(
                            "convert_to_hocr: no context for path %s, skipping",
                            path,
                        )
                        continue
                    page_num, info = context
                    page_to_infos.setdefault(page_num, []).append(info)

        hocr_results: list[hocr.BadgerdocHOCRPageResult] = []
        for page_num, infos in page_to_infos.items():
            logger.info(
                "convert_to_hocr: converting page %d with %d block(s)",
                page_num,
                len(infos),
            )
            hocr_result: hocr.BadgerdocHOCRPageResult = (
                await workflow.execute_activity(
                    deepseek_ocr_2_results_to_hocr,
                    args=[workflow_type, page_num, infos],
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
            )
            hocr_results.append(hocr_result)
            logger.info(
                "convert_to_hocr: page %d → %s", page_num, hocr_result.h_ocr
            )

        logger.info(
            "convert_to_hocr: completed, %d hOCR results produced",
            len(hocr_results),
        )
        return hocr_results
