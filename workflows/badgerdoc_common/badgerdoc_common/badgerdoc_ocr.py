import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from temporalio import workflow

from badgerdoc_common import helpers, hocr, trigger
from badgerdoc_common.activities import document, extraction

logger = logging.getLogger(__name__)


@dataclass
class OCRPageRequest:
    badgerdoc_document: trigger.BadgerdocDocumentPage


@dataclass
class OCRPageContainer:
    pages: list[OCRPageRequest]
    blocks: list[OCRPageRequest]


class BadgerdocOCRBase(ABC):
    """Abstract base class for BadgerDoc OCR workflow implementations.

    Subclasses must implement :meth:`ocr_pages`, :meth:`ocr_blocks`,
    :meth:`align_coordinates`, and :meth:`ocr_merge_blocks`. The concrete
    :meth:`run` method orchestrates all four and returns a flat list of
    :class:`~badgerdoc_common.hocr.BadgerdocHOCRPageResult`.
    """

    @abstractmethod
    async def ocr_pages(
        self,
        params: trigger.DocumentTriggerParams,
        pages: list[OCRPageRequest],
    ) -> list[hocr.BadgerdocOCRPageResult]:
        """Run OCR on full-page renditions."""

    @abstractmethod
    async def ocr_blocks(
        self,
        params: trigger.DocumentTriggerParams,
        blocks: list[OCRPageRequest],
    ) -> list[hocr.BadgerdocOCRPageResult]:
        """Run OCR on sub-page block crops.

        Accepts a list of block :class:`OCRPageRequest` objects, each
        representing a cropped region of a page, and returns OCR results
        for every block.

        **Ordering contract:** the returned list must preserve the same order
        as the input *blocks* list so that each result can be correctly paired
        with its originating block by index (e.g. for coordinate alignment in
        :meth:`align_coordinates`). If OCR fails or produces no output for a
        particular block, an empty
        :class:`~badgerdoc_common.hocr.BadgerdocOCRPageResult` (``ocr={}``) must
        be inserted at the corresponding position rather than omitting the
        entry, to keep the list lengths in sync.
        """

    @abstractmethod
    async def align_coordinates(
        self,
        params: trigger.DocumentTriggerParams,
        block: OCRPageRequest,
        result: hocr.BadgerdocOCRPageResult,
    ) -> hocr.BadgerdocOCRPageResult:
        """Translate block-local OCR coordinates into parent-page space.

        OCR is performed on a cropped block image, so all bounding-box
        coordinates in *result* are relative to the top-left corner of that
        crop. The block image document stores its position within the parent
        page in ``block.badgerdoc_document.document.metadata["position_in_parent"]``
        as the string ``"x1 y1 x2 y2"``. Implementations must shift every
        coordinate in *result* by the crop origin ``(x1, y1)`` so that the
        returned :class:`~badgerdoc_common.hocr.BadgerdocOCRPageResult`
        contains page-absolute coordinates ready for merging with full-page
        results.

        This method is abstract because the internal coordinate representation
        of :class:`~badgerdoc_common.hocr.BadgerdocOCRPageResult` is
        OCR-backend-specific.
        """

    @abstractmethod
    async def ocr_merge_blocks(
        self,
        pages: list[hocr.BadgerdocOCRPageResult],
        blocks: list[hocr.BadgerdocOCRPageResult],
    ) -> list[hocr.BadgerdocOCRPageResult]:
        """Merge block OCR results into their corresponding page results.

        Receives two sources of OCR output:

        - *pages* — one :class:`~badgerdoc_common.hocr.BadgerdocOCRPageResult`
          per full-page rendition, produced by :meth:`ocr_pages`.
        - *blocks* — one :class:`~badgerdoc_common.hocr.BadgerdocOCRPageResult`
          per block crop (already coordinate-aligned to the parent page by
          :meth:`align_coordinates`), produced by :meth:`ocr_blocks`.

        Multiple blocks can belong to the same page, so naively concatenating
        both lists would produce duplicate page keys in the final hOCR output.
        Implementations must fold all block results that share a page key into
        the corresponding page result (or create a new page entry if that page
        has no full-page result), returning a single unified list of
        :class:`~badgerdoc_common.hocr.BadgerdocOCRPageResult` where every
        page appears exactly once.
        """

    @abstractmethod
    async def convert_to_hocr(
        self,
        params: trigger.DocumentTriggerParams,
        results: list[hocr.BadgerdocOCRPageResult],
    ) -> list[hocr.BadgerdocHOCRPageResult]:
        """Convert engine-specific OCR results to the Badgerdoc hOCR format.

        Receives the merged :class:`~badgerdoc_common.hocr.BadgerdocOCRPageResult`
        list produced by :meth:`ocr_merge_blocks` and converts each entry to
        a :class:`~badgerdoc_common.hocr.BadgerdocHOCRPageResult` — the
        normalised, engine-agnostic representation that Badgerdoc consumes.
        This is the final step of the OCR pipeline before results are returned
        from :meth:`run`.
        """

    async def run(
        self,
        params: trigger.DocumentTriggerParams,
        ocr_container: OCRPageContainer,
    ) -> list[hocr.BadgerdocHOCRPageResult]:
        """Orchestrate OCR over all pages and blocks in *ocr_container*.

        Calls :meth:`ocr_pages` and :meth:`ocr_blocks` to produce two streams
        of OCR results, aligns each block result to parent-page coordinates
        via :meth:`align_coordinates`, folds both streams into a single list
        via :meth:`ocr_merge_blocks`, then converts the merged results to the
        Badgerdoc hOCR format via :meth:`convert_to_hocr` and returns them.
        """
        page_results: list[hocr.BadgerdocOCRPageResult] = await self.ocr_pages(
            params, ocr_container.pages
        )
        block_results: list[hocr.BadgerdocOCRPageResult] = (
            await self.ocr_blocks(params, ocr_container.blocks)
        )
        aligned_block_results: list[hocr.BadgerdocOCRPageResult] = [
            await self.align_coordinates(params, block, result)
            for block, result in zip(ocr_container.blocks, block_results)
        ]
        merged_results = await self.ocr_merge_blocks(
            page_results, aligned_block_results
        )
        return await self.convert_to_hocr(params, merged_results)


async def _collect_pages_from_documents(
    docs: list[document.BadgerdocDocument],
) -> dict[tuple[int, int], OCRPageRequest]:
    pages: dict[tuple[int, int], OCRPageRequest] = {}
    for doc in docs:
        renditions_response = await workflow.execute_activity(
            document.badgerdoc_list_documents,
            document.ListDocumentsRequest(
                tags=["rendition"],
                parent_document_id=doc.id,
            ),
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        for rendition_info in renditions_response.documents:
            page_num = (rendition_info.metadata or {}).get("page")
            if page_num is None:
                logger.error(
                    "Rendition document %s has no page in metadata, skipping",
                    rendition_info.id,
                )
                continue
            rendition = await workflow.execute_activity(
                document.badgerdoc_get_rendition,
                args=[doc, page_num],
                start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
            )
            key = (page_num, doc.id)
            pages[key] = OCRPageRequest(
                badgerdoc_document=trigger.BadgerdocDocumentPage(
                    page_num=page_num,
                    document=rendition,
                )
            )
    return pages


async def _collect_pages_from_document_pages(
    doc_pages: list[trigger.BadgerdocDocumentPage],
    existing_pages: dict[tuple[int, int], OCRPageRequest],
) -> dict[tuple[int, int], OCRPageRequest]:
    pages: dict[tuple[int, int], OCRPageRequest] = {}
    for doc_page in doc_pages:
        original_doc_id = (
            doc_page.document.parent_document_id or doc_page.document.id
        )
        key = (doc_page.page_num, original_doc_id)
        if key in existing_pages:
            logger.warning(
                "Page %s for document %s already added from linked_documents, skipping",
                doc_page.page_num,
                original_doc_id,
            )
            continue
        pages[key] = OCRPageRequest(
            badgerdoc_document=trigger.BadgerdocDocumentPage(
                page_num=doc_page.page_num,
                document=doc_page.document,
            )
        )
    return pages


async def _collect_blocks_from_xpaths(
    xpaths: list[extraction.BadgerdocExtractionXpath],
) -> list[OCRPageRequest]:
    async def _fetch_chunk(
        xpath_obj: extraction.BadgerdocExtractionXpath,
    ) -> OCRPageRequest:
        chunk_doc = await workflow.execute_activity(
            document.badgerdoc_get_document_chunk,
            document.DocumentChunkRequest(
                document_id=xpath_obj.extraction_page.document_id,
                page_num=xpath_obj.extraction_page.page_number,
                extraction_id=xpath_obj.extraction_page.extraction_id,
                xpath=xpath_obj.xpath,
            ),
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )
        return OCRPageRequest(
            badgerdoc_document=trigger.BadgerdocDocumentPage(
                page_num=xpath_obj.extraction_page.page_number,
                document=chunk_doc,
            )
        )

    return list(await asyncio.gather(*[_fetch_chunk(x) for x in xpaths]))


async def trigger_params_to_ocr_page(
    params: trigger.DocumentTriggerParams,
) -> OCRPageContainer:
    """
    Convert mixed trigger params into an OCRPageContainer.

    Resolves three input sources into two output collections:

    - ``linked_documents`` — each document is expanded into all its rendition
      pages. Renditions are discovered via the API and fetched individually
      with ``badgerdoc_get_rendition``. Pages are keyed by
      ``(page_num, document_id)`` to enable duplicate detection.

    - ``linked_document_pages`` — explicit page references added directly.
      If a page key already exists from ``linked_documents``, it is skipped
      with a warning to prevent duplicates.

    - ``linked_extraction_xpaths`` — each XPath is resolved to a cropped
      chunk image via ``badgerdoc_get_document_chunk`` and placed in
      ``OCRPageContainer.blocks``, separate from full pages.

    Returns an ``OCRPageContainer`` where ``pages`` contains unique full-page
    renditions for standard OCR and ``blocks`` contains sub-page image crops
    for block-level OCR.
    """
    pages: dict[tuple[int, int], OCRPageRequest] = {}
    blocks: list[OCRPageRequest] = []

    if params.linked_documents:
        pages.update(
            await _collect_pages_from_documents(params.linked_documents)
        )

    if params.linked_document_pages:
        pages.update(
            await _collect_pages_from_document_pages(
                params.linked_document_pages, pages
            )
        )

    if params.linked_extraction_xpaths:
        blocks = await _collect_blocks_from_xpaths(
            params.linked_extraction_xpaths
        )

    return OCRPageContainer(pages=list(pages.values()), blocks=blocks)
