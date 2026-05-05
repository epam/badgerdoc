import logging
from dataclasses import asdict, dataclass
from typing import Any, Literal

from temporalio import activity

from badgerdoc_common import badgerdoc_http
from badgerdoc_common.activities import task

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocExtraction:
    id: int
    document_id: int
    created_by: str
    status: str | None
    temporal_job_id: str | None
    comment: str | None
    tags: list[str]


@dataclass
class CreateExtractionRequest:
    document_id: int
    temporal_job_id: str | None = None
    comment: str | None = None
    task_id: int | None = None
    tags: list[str] | None = None


@dataclass
class FinishExtractionRequest:
    extraction_id: int


@dataclass
class UpdateExtractionRequest:
    extraction_id: int
    temporal_job_id: str | None = None
    comment: str | None = None
    tags: list[str] | None = None


@dataclass
class ListExtractionsRequest:
    document_id: int | None = None
    created_by: str | None = None
    status: str | None = None
    temporal_job_id: str | None = None
    task_id: int | None = None
    tags: list[str] | None = None
    created_at__gte: str | None = None
    created_at__lte: str | None = None
    page: int = 1


@dataclass
class ListExtractionsResponse:
    extractions: list[BadgerdocExtraction]
    next_page: int | None = None


@activity.defn
async def badgerdoc_create_extraction(
    extraction_request: CreateExtractionRequest,
) -> BadgerdocExtraction:
    logger.info("Executing badgerdoc_create_extraction activity")

    payload: dict[str, Any] = {
        "document_id": extraction_request.document_id,
        "status": "Started",
    }

    if extraction_request.temporal_job_id is not None:
        payload["temporal_job_id"] = extraction_request.temporal_job_id
    if extraction_request.comment is not None:
        payload["comment"] = extraction_request.comment
    if extraction_request.tags:
        payload["tags"] = extraction_request.tags

    endpoint = "/badgerdoc/extraction/"

    response_data = await badgerdoc_http.badgerdoc_post(endpoint, payload)
    logger.info("Extraction created: %s", response_data)

    if extraction_request.task_id is not None:
        logger.info(
            "Attaching extraction %s to task %s",
            response_data.get("id"),
            extraction_request.task_id,
        )
        try:
            created_id = response_data["id"]
            task_id = extraction_request.task_id
            # TODO: This could be optimized or lazy loaded
            task_obj = await task.badgerdoc_get_task(task_id)
            extraction_ids = [ext.id for ext in task_obj.extractions]
            await task.badgerdoc_update_task(
                task.BadgerdocTaskUpdateRequest(
                    task_id,
                    extraction_ids=extraction_ids + [created_id],
                )
            )
        except Exception:
            logger.exception(
                "Failed to attach extraction %s to task %s",
                response_data.get("id"),
                extraction_request.task_id,
            )

    try:
        extraction = BadgerdocExtraction(
            id=response_data["id"],
            document_id=response_data["document_id"],
            created_by=response_data["created_by"],
            status=response_data["status"],
            temporal_job_id=response_data.get("temporal_job_id"),
            comment=response_data.get("comment"),
            tags=response_data.get("tags") or [],
        )
    except KeyError:
        logger.warning("Missing key in extraction response: %s", response_data)
        raise

    return extraction


@activity.defn
async def badgerdoc_finish_extraction(
    finish_request: FinishExtractionRequest,
) -> BadgerdocExtraction:
    logger.info("Executing badgerdoc_finish_extraction activity")

    payload = {"status": "Completed"}

    endpoint = f"/badgerdoc/extraction/{finish_request.extraction_id}/"

    response_data = await badgerdoc_http.badgerdoc_patch(endpoint, payload)
    logger.info("Extraction finished: %s", response_data)

    try:
        extraction = BadgerdocExtraction(
            id=response_data["id"],
            document_id=response_data["document_id"],
            created_by=response_data["created_by"],
            status=response_data["status"],
            temporal_job_id=response_data.get("temporal_job_id"),
            comment=response_data.get("comment"),
            tags=response_data.get("tags") or [],
        )
    except KeyError:
        logger.warning("Missing key in extraction response: %s", response_data)
        raise

    return extraction


@activity.defn
async def badgerdoc_update_extraction(
    update_request: UpdateExtractionRequest,
) -> BadgerdocExtraction:
    logger.info("Executing badgerdoc_update_extraction activity")

    payload: dict[str, Any] = {}

    if update_request.temporal_job_id is not None:
        payload["temporal_job_id"] = update_request.temporal_job_id
    if update_request.comment is not None:
        payload["comment"] = update_request.comment
    if update_request.tags is not None:
        payload["tags"] = update_request.tags

    endpoint = f"/badgerdoc/extraction/{update_request.extraction_id}/"

    response_data = await badgerdoc_http.badgerdoc_patch(endpoint, payload)
    logger.info("Extraction updated: %s", response_data)

    try:
        extraction = BadgerdocExtraction(
            id=response_data["id"],
            document_id=response_data["document_id"],
            created_by=response_data["created_by"],
            status=response_data["status"],
            temporal_job_id=response_data.get("temporal_job_id"),
            comment=response_data.get("comment"),
            tags=response_data.get("tags") or [],
        )
    except KeyError:
        logger.warning("Missing key in extraction response: %s", response_data)
        raise

    return extraction


@activity.defn
async def badgerdoc_list_extractions(
    filters: ListExtractionsRequest,
) -> ListExtractionsResponse:
    payload = {
        key: value
        for key, value in asdict(filters).items()
        if value is not None
    }
    if filters.tags:
        payload["tags"] = ",".join(filters.tags)

    endpoint = "/badgerdoc/extractions/"

    try:
        response_data = await badgerdoc_http.badgerdoc_get(endpoint, payload)
        page_extractions = [
            BadgerdocExtraction(
                id=item["id"],
                document_id=item["document_id"],
                created_by=item["created_by"],
                status=item.get("status"),
                temporal_job_id=item.get("temporal_job_id"),
                comment=item.get("comment"),
                tags=item.get("tags") or [],
            )
            for item in response_data["results"]
        ]

        return ListExtractionsResponse(
            extractions=page_extractions,
            next_page=None if not response_data["next"] else filters.page + 1,
        )
    except KeyError as e:
        logger.warning("Missing key in extraction response: %s", e)
        raise


@activity.defn
async def badgerdoc_get_extraction(
    extraction_id: int,
) -> BadgerdocExtraction:
    logger.info("Executing badgerdoc_create_extraction activity")

    endpoint = f"/badgerdoc/extraction/{extraction_id}/"

    response_data = await badgerdoc_http.badgerdoc_get(endpoint)
    logger.info("Extraction found: %s", response_data)
    if not isinstance(response_data, dict):
        raise ValueError(
            f"Expected response_data to be dict, received {type(response_data)}"
        )

    try:
        extraction = BadgerdocExtraction(
            id=response_data["id"],
            document_id=response_data["document_id"],
            created_by=response_data["created_by"],
            status=response_data["status"],
            temporal_job_id=response_data.get("temporal_job_id"),
            comment=response_data.get("comment"),
            tags=response_data.get("tags") or [],
        )
    except KeyError:
        logger.warning("Missing key in extraction response: %s", response_data)
        raise

    return extraction


@dataclass
class BadgerdocExtractionPage:
    id: int
    extraction_id: int
    page_number: int
    content: str | None = None
    document_id: int | None = None


@dataclass
class BadgerdocExtractionXpath:
    extraction_page: BadgerdocExtractionPage
    xpath: str


@dataclass
class CreateExtractionPageRequest:
    extraction_id: int
    page_number: int
    content: dict | None = None


@dataclass
class ListExtractionPagesRequest:
    extraction_id: int | None = None
    page_number: int | None = None
    created_at__gte: str | None = None
    created_at__lte: str | None = None
    page: int = 1
    page_size: int = 10


@dataclass
class GetLatestExtractionPageRequest:
    document_id: int
    page_num: int
    status: (
        None | Literal["Started", "In progress", "Completed", "Timed out"]
    ) = "Completed"
    temporal_job_id: None | str = None
    tags: None | list[str] = None


@dataclass
class GetExtractionPageByExtractionAndPageRequest:
    extraction_id: int
    page_number: int


@dataclass
class ListExtractionPagesResponse:
    extraction_pages: list[BadgerdocExtractionPage]
    next_page: int | None = None


@activity.defn
async def badgerdoc_create_extraction_page(
    page_request: CreateExtractionPageRequest,
) -> BadgerdocExtractionPage:
    logger.info("Executing badgerdoc_create_extraction_page activity")

    payload = {
        key: value
        for key, value in asdict(page_request).items()
        if value is not None
    }

    endpoint = "/badgerdoc/extraction-page/"

    response_data = await badgerdoc_http.badgerdoc_post(endpoint, payload)
    logger.info("Extraction page created: %s", response_data)

    try:
        extraction_page = BadgerdocExtractionPage(
            id=response_data["id"],
            extraction_id=response_data["extraction_id"],
            page_number=response_data["page_number"],
            content=response_data.get("content"),
        )
    except KeyError:
        logger.warning(
            "Missing key in extraction page response: %s", response_data
        )
        raise

    return extraction_page


@activity.defn
async def badgerdoc_list_extraction_pages(
    filters: ListExtractionPagesRequest,
) -> ListExtractionPagesResponse:
    payload = {
        key: value
        for key, value in asdict(filters).items()
        if value is not None
    }

    endpoint = "/badgerdoc/extraction-pages/"

    try:
        response_data = await badgerdoc_http.badgerdoc_get(endpoint, payload)
        pages = [
            BadgerdocExtractionPage(
                id=item["id"],
                extraction_id=item["extraction_id"],
                page_number=item["page_number"],
                content=item.get("content"),
                document_id=item.get("document_id"),
            )
            for item in response_data["results"]
        ]

        return ListExtractionPagesResponse(
            extraction_pages=pages,
            next_page=None if not response_data["next"] else filters.page + 1,
        )
    except KeyError as e:
        logger.warning("Missing key in extraction page response: %s", e)
        raise


@activity.defn
async def badgerdoc_get_latest_extraction_page(
    filters: GetLatestExtractionPageRequest,
) -> BadgerdocExtractionPage:
    endpoint = f"/badgerdoc/document/{filters.document_id}/extraction-page/latest/{filters.page_num}/"
    payload = {
        "status": filters.status,
        "temporal_job_id": filters.temporal_job_id,
        "tags": filters.tags,
    }
    response_data = await badgerdoc_http.badgerdoc_get(
        endpoint,
        {key: value for key, value in payload.items() if value},
    )
    logger.info("Latest extraction page retrieved: %s", response_data)

    try:
        extraction_page = BadgerdocExtractionPage(
            id=response_data["id"],
            extraction_id=response_data["extraction_id"],
            page_number=response_data["page_number"],
            content=response_data.get("content"),
            document_id=response_data.get("document_id"),
        )
    except KeyError:
        logger.warning(
            "Missing key in latest extraction page response: %s", response_data
        )
        raise

    return extraction_page


@activity.defn
async def badgerdoc_get_extraction_page(
    page_id: int,
) -> BadgerdocExtractionPage:
    logger.info("Executing badgerdoc_get_extraction_page activity")

    endpoint = f"/badgerdoc/extraction-page/{page_id}/"

    response_data = await badgerdoc_http.badgerdoc_get(endpoint)
    logger.info("Extraction page retrieved: %s", response_data)

    try:
        extraction_page = BadgerdocExtractionPage(
            id=response_data["id"],
            extraction_id=response_data["extraction_id"],
            page_number=response_data["page_number"],
            content=response_data.get("content"),
            document_id=response_data.get("document_id"),
        )
    except KeyError as e:
        logger.warning("Missing key in extraction page response: %s", e)
        raise

    return extraction_page


@activity.defn
async def badgerdoc_get_extraction_page_by_extraction_and_page(
    filters: GetExtractionPageByExtractionAndPageRequest,
) -> BadgerdocExtractionPage:
    logger.info(
        "Executing badgerdoc_get_extraction_page_by_extraction_and_page activity"
    )

    endpoint = "/badgerdoc/extraction-pages/"
    payload = {
        "extraction_id": filters.extraction_id,
        "page_number": filters.page_number,
    }

    response_data = await badgerdoc_http.badgerdoc_get(endpoint, payload)
    logger.info(
        "Extraction page by extraction and page retrieved: %s", response_data
    )

    if not response_data or not isinstance(response_data, dict):
        raise ValueError(f"Invalid response from API: {response_data}")

    results = response_data.get("results", [])
    if not results:
        raise ValueError(
            f"No extraction page found for extraction_id={filters.extraction_id}, "
            f"page_number={filters.page_number}"
        )

    page_data = results[0]
    try:
        extraction_page = BadgerdocExtractionPage(
            id=page_data["id"],
            extraction_id=page_data["extraction_id"],
            page_number=page_data["page_number"],
            content=page_data.get("content"),
            document_id=page_data.get("document_id"),
        )
    except KeyError as e:
        logger.warning("Missing key in extraction page response: %s", e)
        raise

    return extraction_page
