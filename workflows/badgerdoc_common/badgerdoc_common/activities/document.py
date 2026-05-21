import json
import logging
import urllib.parse
from dataclasses import asdict, dataclass, field
from io import BytesIO
from typing import Any, BinaryIO

import aiohttp
from temporalio import activity

from badgerdoc_common import badgerdoc_http

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocDocument:
    name: str | None = None
    extension: str | None = None
    metadata: dict[str, Any] | None = None
    tags: list[str] | None = None
    parent_document_id: int | None = None
    id: int | None = None
    file: str | None = None
    uploaded_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class ListDocumentsRequest:
    tags: list[str] | None = None
    parent_document_id: int | None = None
    metadata_field: dict[str, Any] = field(default_factory=dict)
    page: int = 1


@dataclass
class ListDocumentsResponse:
    documents: list[BadgerdocDocument]
    count: int


def _parse_document(document_json: dict[str, Any]) -> BadgerdocDocument:
    return BadgerdocDocument(
        id=document_json.get("id"),
        name=document_json.get("name"),
        file=document_json.get("file"),
        extension=(
            str(document_json.get("extension"))
            if document_json.get("extension")
            else None
        ),
        tags=document_json.get("tags"),
        metadata=document_json.get("metadata"),
        parent_document_id=document_json.get("parent_document_id"),
        uploaded_by=document_json.get("uploaded_by"),
        created_at=document_json.get("created_at"),
        updated_at=document_json.get("updated_at"),
    )


def _document_to_form(document: BadgerdocDocument) -> aiohttp.FormData:
    payload: dict[str, Any] = {
        key: value
        for key, value in asdict(document).items()
        if value is not None
    }

    form = aiohttp.FormData()
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            form.add_field(key, json.dumps(value))
        elif not isinstance(value, (BytesIO)):
            form.add_field(key, str(value))

    return form


@activity.defn
async def badgerdoc_create_document(
    document: BadgerdocDocument,
) -> BadgerdocDocument:
    """Create a document record (without uploading file content)."""
    logger.info("Creating document record: %s", document.name)

    try:
        form = _document_to_form(document)
        document_data = await badgerdoc_http.badgerdoc_form_post(
            "/badgerdoc/document/", form
        )

        logger.info(
            "Document created successfully: %s", document_data.get("id")
        )
        if not document_data.get("id"):
            raise ValueError("Document creation succeeded but no id returned")

        return _parse_document(document_data)
    except Exception as e:
        logger.warning(
            "Failed to create document %s: %s", document.name, str(e)
        )
        raise


@activity.defn
async def badgerdoc_list_documents(
    filters: ListDocumentsRequest,
) -> ListDocumentsResponse:
    if isinstance(filters, dict):
        filters = ListDocumentsRequest(**filters)
    all_documents: list[BadgerdocDocument] = []
    page = 1
    has_next = True

    payload: dict[str, str] = {}
    if filters.tags is not None:
        payload["tags"] = ",".join(filters.tags)

    if filters.parent_document_id is not None:
        payload["parent_document_id"] = str(filters.parent_document_id)

    if filters.metadata_field is not None:
        payload["metadata"] = json.dumps(filters.metadata_field)

    while has_next:
        payload["page"] = str(page)

        endpoint = "/badgerdoc/documents/"
        try:
            response_data = await badgerdoc_http.badgerdoc_get(
                endpoint, params=payload
            )
            page_documents = [
                _parse_document(item) for item in response_data["results"]
            ]
            all_documents.extend(page_documents)

            has_next = bool(response_data.get("next"))
            if has_next:
                page += 1
        except Exception as e:
            logger.warning("Failed to request documents: %s", str(e))
            raise

    return ListDocumentsResponse(
        documents=all_documents, count=len(all_documents)
    )


@activity.defn
async def badgerdoc_update_document(
    document_id: int, updates: BadgerdocDocument
) -> BadgerdocDocument:
    """Update a document by id (partial update) and return the updated document."""
    logger.info("Updating document %s with: %s", document_id, updates)

    try:
        endpoint = f"/badgerdoc/document/{document_id}/"
        form = _document_to_form(updates)

        document_data = await badgerdoc_http.badgerdoc_form_patch(
            endpoint, form
        )

        logger.info(
            "Document updated successfully: %s", document_data.get("id")
        )
        return _parse_document(document_data)
    except Exception as e:
        logger.warning("Failed to update document %s: %s", document_id, str(e))
        raise


async def badgerdoc_upload_document(
    document: BadgerdocDocument, file: BinaryIO
) -> BadgerdocDocument:
    logger.info("Uploading document: %s", document.name)

    filename = f"{str(document.name)[:50]}.{document.extension}"

    try:
        form = _document_to_form(document)
        form.add_field("file", file, filename=filename)
        document_data = await badgerdoc_http.badgerdoc_form_post(
            "/badgerdoc/document/", form
        )
        logger.info(
            "Document uploaded successfully: %s",
            document_data.get("id"),
        )

        if not document_data.get("id"):
            raise ValueError(
                "Document upload succeeded but no document data returned"
            )

        return _parse_document(document_data)
    except Exception as e:
        logger.warning(
            "Failed to upload document %s: %s", document.name, str(e)
        )
        raise


async def badgerdoc_upload_file(
    document: BadgerdocDocument, file: BinaryIO
) -> BadgerdocDocument:
    logger.info("Uploading document: %s", document.name)

    filename = f"{str(document.name)[:50]}.{document.extension}"

    try:
        form = aiohttp.FormData()
        form.add_field("file", file, filename=filename)
        form.add_field("extension", str(document.extension))
        document_data = await badgerdoc_http.badgerdoc_form_patch(
            f"/badgerdoc/document/{document.id}/", form
        )
        logger.info(
            "Document uploaded successfully: %s",
            document_data.get("id"),
        )

        if not document_data.get("id"):
            raise ValueError(
                "Document upload succeeded but no document data returned"
            )

        return _parse_document(document_data)
    except Exception as e:
        logger.warning(
            "Failed to upload document %s: %s", document.name, str(e)
        )
        raise


@activity.defn
async def badgerdoc_get_document(document_id: int) -> BadgerdocDocument:
    logger.info("Getting document: %s", document_id)

    try:
        endpoint = f"/badgerdoc/document/{document_id}/"
        document_data = await badgerdoc_http.badgerdoc_get(endpoint)
        if not isinstance(document_data, dict):
            raise ValueError(
                f"Expected response to be a dict, got {type(document_data)} instead"
            )

        logger.info(
            "Document retrieved successfully: %s", document_data.get("id")
        )

        return _parse_document(document_data)
    except Exception as e:
        logger.warning("Failed to get document %s: %s", document_id, str(e))
        raise


@activity.defn
async def badgerdoc_get_rendition(
    document: BadgerdocDocument, page: int
) -> BadgerdocDocument:
    if isinstance(document, dict):
        document = BadgerdocDocument(**document)
    logger.info(
        "Getting rendition for document %s, page %s", document.id, page
    )

    endpoint = f"/badgerdoc/document/{document.id}/rendition-page/{page}/"
    document_data = await badgerdoc_http.badgerdoc_get(endpoint)
    if not isinstance(document_data, dict):
        raise ValueError(
            f"Expected response to be a dict, got {type(document_data)} instead"
        )

    logger.info(
        "Rendition retrieved successfully: %s", document_data.get("id")
    )

    return _parse_document(document_data)


@activity.defn
async def badgerdoc_delete_document(document_id: int) -> None:
    """Delete a document by id."""
    logger.info("Deleting document: %s", document_id)

    try:
        endpoint = f"/badgerdoc/document/{document_id}/"
        await badgerdoc_http.badgerdoc_delete(endpoint)

        logger.info("Document deleted successfully: %s", document_id)
    except Exception as e:
        logger.warning("Failed to delete document %s: %s", document_id, str(e))
        raise


@dataclass
class DocumentChunkRequest:
    document_id: int
    page_num: int
    extraction_id: int
    xpath: str


@activity.defn
async def badgerdoc_get_document_chunk(
    request: DocumentChunkRequest,
) -> BadgerdocDocument:
    if isinstance(request, dict):
        request = DocumentChunkRequest(**request)
    logger.info(
        "Getting document chunk for document %s, page %s, extraction %s",
        request.document_id,
        request.page_num,
        request.extraction_id,
    )

    encoded_xpath = urllib.parse.quote(request.xpath, safe="")
    endpoint = (
        f"/badgerdoc/document/{request.document_id}/chunk"
        f"/page/{request.page_num}"
        f"/extraction/{request.extraction_id}"
        f"/xpath/{encoded_xpath}"
    )

    try:
        document_data = await badgerdoc_http.badgerdoc_get(endpoint)
        if not isinstance(document_data, dict):
            raise ValueError(
                f"Expected response to be a dict, got {type(document_data)} instead"
            )

        logger.info(
            "Document chunk retrieved successfully: %s",
            document_data.get("id"),
        )

        return _parse_document(document_data)
    except Exception as e:
        logger.warning(
            "Failed to get document chunk for document %s: %s",
            request.document_id,
            str(e),
        )
        raise
