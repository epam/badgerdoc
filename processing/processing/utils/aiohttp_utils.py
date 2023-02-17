import asyncio
from typing import Any, Dict, NamedTuple

import aiohttp
from aiohttp import ContentTypeError
from fastapi import HTTPException
from processing.config import settings
from processing.utils.logger import get_logger

logger = get_logger(__name__)

Response = NamedTuple(
    "Response", [("status_code", int), ("json", Dict[Any, Any])]
)


async def send_request(method: str, url: str, **kwargs: Any) -> Response:
    http_session = aiohttp.ClientSession(
        raise_for_status=False,
        timeout=aiohttp.ClientTimeout(total=settings.request_timeout),
    )
    logger.info("Send request to %s. %s, %s", url, method, kwargs)
    for attempt in range(settings.retry_attempts):
        async with http_session.request(
            method=method, url=url, **kwargs
        ) as resp:
            if resp.status in settings.retry_statuses:
                logger.error("Bad status code: %s from %s", resp.status, url)
                if attempt != settings.retry_attempts - 1:
                    await asyncio.sleep(settings.delay_between_retry_attempts)
                continue

            try:
                response_data = await resp.json()
            except ContentTypeError:
                response_data = await resp.read()

            if resp.status not in {i for i in range(200, 300)}:
                raise HTTPException(
                    500, f"Can't get response from {url}: `{response_data}`"
                )

            logger.info("Get data successful")
            return Response(status_code=resp.status, json=response_data)

    raise HTTPException(500, f"Can't get response from {url}")
