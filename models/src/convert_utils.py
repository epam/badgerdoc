import logging
import traceback
from typing import NoReturn

import requests
from fastapi import HTTPException
from requests import ConnectionError, RequestException, Timeout

from src.constants import CONVERT_EXPORT_URL, HEADER_TENANT
from src.schemas import ConvertRequestSchema

LOGGER = logging.getLogger(name="models")


def prepare_dataset_info(
    convert_request: ConvertRequestSchema, tenant: str, token: str
) -> str:
    try:
        convert_response = requests.post(
            CONVERT_EXPORT_URL,
            headers={
                HEADER_TENANT: tenant,
                "Authorization": f"Bearer {token}",
            },
            json=convert_request.dict(),
            timeout=100,
        )
    except (ConnectionError, RequestException, Timeout):
        raise_request_exception(traceback.format_exc())
    if convert_response.status_code not in [200, 201]:
        raise_request_exception(convert_response.text)
    minio_path: str = convert_response.json().get("minio_path")
    if not minio_path:
        raise_request_exception("Dataset creation error")
    return minio_path


def raise_request_exception(error_message: str) -> NoReturn:
    LOGGER.info("Convert service error: %s", error_message)
    raise HTTPException(status_code=500, detail=f"Error: {error_message}")
