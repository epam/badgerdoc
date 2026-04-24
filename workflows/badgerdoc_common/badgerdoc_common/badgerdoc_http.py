import logging
import os
from typing import Any, BinaryIO

import aiohttp

logger = logging.getLogger(__name__)

TEMPORAL_BADGERDOC_ADDRESS = os.environ.get("TEMPORAL_BADGERDOC_ADDRESS", "")
BADGERDOC_TOKEN = os.environ.get("BADGERDOC_TOKEN", "")


class BadgerdocAPIError(aiohttp.ClientResponseError):
    """Base class for Badgerdoc API response errors."""


class BadgerdocDoesNotExist(BadgerdocAPIError):
    """Raised when the requested resource does not exist (HTTP 404)."""


class BadgerdocUserError(BadgerdocAPIError):
    """Raised for client-side errors (HTTP 4xx except 404)."""


class BadgerdocInternalError(BadgerdocAPIError):
    """Raised for server-side errors (HTTP 500)."""


def _raise_mapped_response_error(
    response: aiohttp.ClientResponse,
    response_text: str,
    action: str = "Request",
) -> None:
    status = response.status
    message = f"{action} failed: {response_text}"
    headers = getattr(response, "headers", None)

    if status == 404:
        raise BadgerdocDoesNotExist(
            response.request_info,
            response.history,
            status=status,
            message=message,
            headers=headers,
        )
    if 400 <= status < 500:
        raise BadgerdocUserError(
            response.request_info,
            response.history,
            status=status,
            message=message,
            headers=headers,
        )
    if status == 500:
        raise BadgerdocInternalError(
            response.request_info,
            response.history,
            status=status,
            message=message,
            headers=headers,
        )

    raise aiohttp.ClientResponseError(
        request_info=response.request_info,
        history=response.history,
        status=response.status,
        message=f"Request failed: {response_text}",
    )


async def _make_json_request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.info("Making %s request to Badgerdoc: %s", method, url)
    logger.info("Payload: %s", payload)
    logger.info("Params: %s", params)

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
            params=params,
            allow_redirects=True,
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
                _raise_mapped_response_error(
                    response, response_text, action=method
                )

            return await response.json()


async def _make_form_request(
    method: str, url: str, form: aiohttp.FormData
) -> dict[str, Any]:
    logger.info("Making %s form request to Badgerdoc: %s", method, url)

    if not BADGERDOC_TOKEN:
        logger.warning("Badgerdoc token seems empty")

    if not url.startswith("/"):
        raise ValueError("URL must start with '/'")

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Token {BADGERDOC_TOKEN}"}

        async with session.request(
            method,
            f"{TEMPORAL_BADGERDOC_ADDRESS}{url}",
            data=form,
            headers=headers,
        ) as response:
            logger.info("%s response status: %s", method, response.status)
            logger.debug("%s response headers: %s", method, response.headers)

            response_text = await response.text()
            logger.debug("%s response body: %s", method, response_text)

            if response.status >= 400:
                logger.error(
                    "%s form request failed. Status: %s, Response: %s",
                    method,
                    response.status,
                    response_text,
                )
                _raise_mapped_response_error(
                    response, response_text, action=f"{method} form"
                )

            return await response.json()


async def badgerdoc_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _make_json_request("POST", url, payload=payload)


async def badgerdoc_patch(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _make_json_request("PATCH", url, payload=payload)


async def badgerdoc_get(
    url: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]] | dict[str, Any]:
    return await _make_json_request("GET", url, params=params)


async def badgerdoc_delete(
    url: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]] | dict[str, Any]:
    return await _make_json_request("DELETE", url, params=params)


async def badgerdoc_form_post(
    url: str, form: aiohttp.FormData
) -> dict[str, Any]:
    return await _make_form_request("POST", url, form)


async def badgerdoc_form_patch(
    url: str, form: aiohttp.FormData
) -> dict[str, Any]:
    return await _make_form_request("PATCH", url, form)


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
        async with session.get(
            file_url, headers=headers, allow_redirects=True
        ) as response:
            logger.info("Download response status: %s", response.status)
            logger.debug("Download response headers: %s", response.headers)

            if response.status >= 400:
                response_text = await response.text()
                logger.error(
                    "Failed to download document file. Status: %s, Response: %s",
                    response.status,
                    response_text,
                )
                _raise_mapped_response_error(
                    response, response_text, action="Download"
                )

            async for chunk in response.content.iter_chunked(8192):
                buffer.write(chunk)

    buffer.seek(0)
    logger.info("Document file downloaded successfully")
