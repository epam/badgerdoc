import logging
from dataclasses import asdict, dataclass

from temporalio import activity

from badgerdoc_common import badgerdoc_http

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocExtractionDocument:
    id: int
    extraction_id: int
    content: dict | None


@dataclass
class CreateExtractionDocumentRequest:
    extraction_id: int
    content: dict | None


@dataclass
class UpdateExtractionDocumentRequest:
    extraction_id: int
    content: dict | None = None


@activity.defn
async def badgerdoc_create_extraction_document(
    request_data: CreateExtractionDocumentRequest,
) -> BadgerdocExtractionDocument:
    logger.info("Executing badgerdoc_create_extraction_document activity")

    payload = {
        key: value
        for key, value in asdict(request_data).items()
        if value is not None and key != "extraction_id"
    }

    endpoint = f"/badgerdoc/extraction/{request_data.extraction_id}/extraction-document/"

    response_data = await badgerdoc_http.badgerdoc_post(endpoint, payload)
    logger.info("Extraction document created: %s", response_data)

    try:
        extraction_document = BadgerdocExtractionDocument(
            id=response_data["id"],
            extraction_id=response_data["extraction_id"],
            content=response_data.get("content"),
        )
    except KeyError:
        logger.warning(
            "Missing key in extraction document response: %s", response_data
        )
        raise

    return extraction_document


@activity.defn
async def badgerdoc_update_extraction_document(
    request_data: UpdateExtractionDocumentRequest,
) -> BadgerdocExtractionDocument:
    logger.info("Executing badgerdoc_update_extraction_document activity")

    payload = {
        key: value
        for key, value in asdict(request_data).items()
        if value is not None and key != "extraction_id"
    }

    endpoint = f"/badgerdoc/extraction/{request_data.extraction_id}/extraction-document/"

    response_data = await badgerdoc_http.badgerdoc_patch(endpoint, payload)
    logger.info("Extraction document updated: %s", response_data)

    try:
        extraction_document = BadgerdocExtractionDocument(
            id=response_data["id"],
            extraction_id=response_data["extraction_id"],
            content=response_data.get("content"),
        )
    except KeyError:
        logger.warning(
            "Missing key in extraction document response: %s", response_data
        )
        raise

    return extraction_document


@activity.defn
async def badgerdoc_get_extraction_document(
    extraction_id: int,
) -> BadgerdocExtractionDocument:
    logger.info("Executing badgerdoc_update_extraction_document activity")

    endpoint = f"/badgerdoc/extraction/{extraction_id}/extraction-document/"

    response_data = await badgerdoc_http.badgerdoc_get(endpoint)
    logger.info("Extraction document updated: %s", response_data)

    if not isinstance(response_data, dict):
        raise ValueError(
            f"Expected response_data to be dict, received {type(response_data)}"
        )

    try:
        extraction_document = BadgerdocExtractionDocument(
            id=response_data["id"],
            extraction_id=response_data["extraction_id"],
            content=response_data.get("content"),
        )
    except KeyError:
        logger.warning(
            "Missing key in extraction document response: %s", response_data
        )
        raise

    return extraction_document
