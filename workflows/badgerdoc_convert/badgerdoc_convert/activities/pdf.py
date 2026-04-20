import logging
from dataclasses import dataclass
from io import BytesIO

import pdfplumber
from temporalio import activity

from badgerdoc_common import badgerdoc_http
from badgerdoc_common.activities.document import (
    ListDocumentsRequest,
    badgerdoc_delete_document,
    badgerdoc_get_document,
    badgerdoc_list_documents,
)

logger = logging.getLogger(__name__)

IMAGE_RESOLUTION_DPI = 750  # TODO: add to the configutation


class BadgerdocPNGUtilsError(Exception):
    pass


@dataclass
class PDFConvertResult:
    pages_converted: int
    pages_statuses: list[bool]


async def clear_existing_renditions(document_id: int) -> None:
    logger.info("Deleting renditions for document: %s", document_id)
    list_request = ListDocumentsRequest(
        tags=["rendition"], parent_document_id=document_id
    )
    existing_docs = await badgerdoc_list_documents(list_request)
    logger.info("Found %d rendition documents to delete", existing_docs.count)

    for existing_doc in existing_docs.documents:
        logger.info(
            "Deleting existing rendition document: %s", existing_doc.id
        )
        await badgerdoc_delete_document(existing_doc.id)


@activity.defn
async def download_and_convert_document(document_id: int) -> PDFConvertResult:
    await clear_existing_renditions(document_id)

    document = await badgerdoc_get_document(document_id)
    buffer = BytesIO()
    await badgerdoc_http.badgerdoc_download(buffer, document)

    logger.info(
        "Document downloaded to buffer. Size: %d bytes", len(buffer.getvalue())
    )
    pages_statuses = []
    page_num = 0
    with pdfplumber.open(buffer) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            image = page.to_image(resolution=IMAGE_RESOLUTION_DPI).original
            width, height = image.size
            filename = f"{document_id}_page_{page_num}.png"
            imbuffer = BytesIO()
            image.save(imbuffer, format="PNG")
            imbuffer.seek(0)
            new_document = await badgerdoc_http.badgerdoc_upload(
                imbuffer,
                filename,
                metadata={"page": page_num, "width": width, "height": height},
                tags=["rendition"],
                parent_document_id=document_id,
                extension="png",
            )
            imbuffer.truncate(0)
            logger.info(
                "Image of page %s uploaded successfully: %s",
                page_num,
                new_document.get("id"),
            )
            pages_statuses.append(True)
        return PDFConvertResult(
            pages_converted=page_num, pages_statuses=pages_statuses
        )
