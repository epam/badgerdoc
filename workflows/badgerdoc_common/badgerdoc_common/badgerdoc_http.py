import json
import logging
import os
from typing import Any, BinaryIO

import aiohttp

logger = logging.getLogger(__name__)

TEMPORAL_BADGERDOC_ADDRESS = os.environ.get("TEMPORAL_BADGERDOC_ADDRESS", "")
BADGERDOC_TOKEN = os.environ.get("BADGERDOC_TOKEN", "")


async def badgerdoc_get(
    url: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]] | dict[str, Any]:
    logger.info(
        "Getting workflows from Badgerdoc: %s", TEMPORAL_BADGERDOC_ADDRESS
    )

    if not BADGERDOC_TOKEN:
        logger.warning("Badgerdoc token seems empty")

    if not url.startswith("/"):
        raise ValueError("URL must start with '/'")

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Token {BADGERDOC_TOKEN}"}
        async with session.get(
            f"{TEMPORAL_BADGERDOC_ADDRESS}{url}",
            headers=headers,
            params=params,
        ) as response:
            logger.info("Response status: %s", response.status)
            logger.debug("Response headers: %s", response.headers)
            response_text = await response.text()
            logger.debug("Response body: %s", response_text)

            if response.status >= 400:
                logger.error(
                    "Request failed with status %s: %s",
                    response.status,
                    response_text,
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Request failed: {response_text}",
                )

            return json.loads(response_text)


async def badgerdoc_upload(
    file: BinaryIO,
    filename: str,
    metadata: dict | None = None,
    tags: list[str] | None = None,
    parent_document_id: int | None = None,
    extension: str | None = None,
) -> dict[str, Any]:
    logger.info("Uploading document to Badgerdoc: %s", filename)

    if not BADGERDOC_TOKEN:
        logger.warning("Badgerdoc token seems empty")

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Token {BADGERDOC_TOKEN}"}

        data = aiohttp.FormData()
        data.add_field("file", file, filename=filename)

        if metadata:
            data.add_field("metadata", json.dumps(metadata))

        if tags:
            data.add_field("tags", json.dumps(tags))

        if parent_document_id:
            data.add_field("parent_document_id", str(parent_document_id))

        if extension:
            data.add_field("extension", str(extension))

        async with session.post(
            f"{TEMPORAL_BADGERDOC_ADDRESS}/badgerdoc/document/",
            data=data,
            headers=headers,
        ) as response:
            logger.info("Upload response status: %s", response.status)
            logger.debug("Upload response headers: %s", response.headers)

            response_text = await response.text()
            logger.debug("Upload response body: %s", response_text)

            if response.status >= 400:
                logger.error(
                    "Failed to upload document. Status: %s, Response: %s",
                    response.status,
                    response_text,
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Upload failed: {response_text}",
                )

            return await response.json()


async def _make_json_request(
    method: str, url: str, payload: dict[str, Any]
) -> dict[str, Any]:
    logger.info("Making %s request to Badgerdoc: %s", method, url)
    logger.info("Payload: %s", payload)

    if not BADGERDOC_TOKEN:
        logger.warning("Badgerdoc token seems empty")

    if not url.startswith("/"):
        raise ValueError("URL must start with '/'")

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Token {BADGERDOC_TOKEN}",
            "Content-Type": "application/json",
        }

        async with session.request(
            method,
            f"{TEMPORAL_BADGERDOC_ADDRESS}{url}",
            json=payload,
            headers=headers,
        ) as response:
            logger.info("%s response status: %s", method, response.status)
            logger.debug("%s response headers: %s", method, response.headers)

            response_text = await response.text()
            logger.debug("%s response body: %s", method, response_text)

            if response.status >= 400:
                logger.error(
                    "%s request failed. Status: %s, Response: %s",
                    method,
                    response.status,
                    response_text,
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"{method} request failed: {response_text}",
                )

            return await response.json()


async def badgerdoc_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _make_json_request("POST", url, payload)


async def badgerdoc_patch(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _make_json_request("PATCH", url, payload)


async def badgerdoc_delete(url: str) -> None:
    logger.info("Making DELETE request to Badgerdoc: %s", url)

    if not BADGERDOC_TOKEN:
        logger.warning("Badgerdoc token seems empty")

    if not url.startswith("/"):
        raise ValueError("URL must start with '/'")

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Token {BADGERDOC_TOKEN}"}

        async with session.delete(
            f"{TEMPORAL_BADGERDOC_ADDRESS}{url}",
            headers=headers,
        ) as response:
            logger.info("DELETE response status: %s", response.status)
            logger.debug("DELETE response headers: %s", response.headers)

            if response.status >= 400:
                response_text = await response.text()
                logger.error(
                    "DELETE request failed. Status: %s, Response: %s",
                    response.status,
                    response_text,
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"DELETE request failed: {response_text}",
                )


async def badgerdoc_download(buffer: BinaryIO, document: Any) -> None:
    if not document.file:
        raise ValueError("Document file URL is required for download")

    logger.info("Downloading document file: %s", document.file)

    if not BADGERDOC_TOKEN:
        logger.warning("Badgerdoc token seems empty")

    buffer.seek(0)
    buffer.truncate(0)

    file_url = document.file
    if not file_url.startswith("http"):
        if not file_url.startswith("/"):
            file_url = f"/{file_url}"
        file_url = f"{TEMPORAL_BADGERDOC_ADDRESS}{file_url}"

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Token {BADGERDOC_TOKEN}"}
        async with session.get(file_url, headers=headers) as response:
            logger.info("Download response status: %s", response.status)
            logger.debug("Download response headers: %s", response.headers)

            if response.status >= 400:
                response_text = await response.text()
                logger.error(
                    "Failed to download document file. Status: %s, Response: %s",
                    response.status,
                    response_text,
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Download failed: {response_text}",
                )

            async for chunk in response.content.iter_chunked(8192):
                buffer.write(chunk)

    buffer.seek(0)
    logger.info("Document file downloaded successfully")


async def badgerdoc_update_file(
    document_id: int, file: BinaryIO, filename: str, extension: str
) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Token {BADGERDOC_TOKEN}"}

        data = aiohttp.FormData()
        data.add_field("file", file, filename=filename)
        data.add_field("extension", str(extension))

        async with session.patch(
            f"{TEMPORAL_BADGERDOC_ADDRESS}/badgerdoc/document/{document_id}/",
            data=data,
            headers=headers,
        ) as response:
            response_text = await response.text()
            if response.status >= 400:
                logger.error(
                    "Failed to upload document file. Status: %s, Response: %s",
                    response.status,
                    response_text,
                )
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Upload failed: {response_text}",
                )

            return await response.json()
