import logging
from io import BytesIO

from temporalio import activity

from badgerdoc_common.activities import extraction
from badgerdoc_common.hocr import BadgerdocHOCRPageResult

logger = logging.getLogger(__name__)


@activity.defn
async def create_extraction_page(
    extraction_id: int,
    hocr_result: BadgerdocHOCRPageResult,
) -> list[extraction.BadgerdocExtractionPage]:
    from badgerdoc_common import storage

    logger.info(
        "Executing create_extraction_page activity for extraction_id=%s",
        extraction_id,
    )

    created_pages = []

    for page_number, hocr_path in hocr_result.h_ocr.items():
        logger.info(
            "Processing page %s with hOCR path: %s", page_number, hocr_path
        )

        hocr_buffer = BytesIO()
        await storage.badgerdoc_download(hocr_buffer, hocr_path)
        hocr_buffer.seek(0)
        hocr_content = hocr_buffer.read().decode("utf-8")

        page_request = extraction.CreateExtractionPageRequest(
            extraction_id=extraction_id,
            page_number=page_number,
            content=hocr_content,
        )

        extraction_page = await extraction.badgerdoc_create_extraction_page(
            page_request
        )

        logger.info(
            "Created extraction page %s for page number %s",
            extraction_page.id,
            page_number,
        )
        created_pages.append(extraction_page)

    logger.info(
        "Successfully created %d extraction pages for extraction_id=%s",
        len(created_pages),
        extraction_id,
    )

    return created_pages
