import time
from typing import Any, Dict, List, Optional

import requests

from src import config, log, schemas, service_token

logger = log.get_logger(__file__)


def make_request(
    url: str,
    body: Optional[Dict[str, Any]] = None,
    data: Any = None,
    method: str = "PUT",
    headers: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make request and return response payload."""
    logger.info(
        f"Sending request to url: {url} with method: {method} "
        f"headers: {log.cut_dict_strings(headers)} body: {body} data: {data}"
    )
    response = requests.request(
        method=method, url=url, json=body, data=data, headers=headers
    )
    response.raise_for_status()
    return response


def make_request_with_retry(
    url: str,
    body: Optional[Dict[str, Any]] = None,
    data: Any = None,
    method: str = "PUT",
    retries: int = 3,
    start: int = 1,
    headers: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make request and retry if failed."""
    _ratio = 1.66
    if retries <= 0:
        raise ValueError("Retries value must be greater than 0.")
    for sleep_t in (start * _ratio**i for i in range(retries)):
        try:
            return make_request(
                url=url, body=body, data=data, method=method, headers=headers
            )
        except Exception:
            logger.exception(
                f"Error while making request to {url}. "
                f"Sleeping for retry: {sleep_t} sec."
            )
            time.sleep(sleep_t)
    logger.warning(f"Maximum number of retries reached for {url}.")
    return None


def get_file_status(file_id: int, tenant: str) -> Optional[schemas.PreprocessingStatus]:
    logger.info(f"Sending request to the assets to get file {file_id} status.")
    body = {"filters": [{"field": "id", "operator": "eq", "value": file_id}]}
    url = f"{config.ASSETS_URI}/files/search"
    token = service_token.get_service_token()
    headers = {
        "X-Current-Tenant": tenant,
        "Authorization": f"Bearer {token}",
    }
    response = make_request_with_retry(
        url=url, body=body, method="POST", headers=headers
    )
    if response is None:
        return None
    try:
        file_status = response.json()["data"][0]["status"]
    except Exception:
        logger.exception("Error while extracting file status from response.")
        return None
    return file_status  # type:ignore


def get_model_types(model_ids: List[str]) -> Dict[str, str]:
    body = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [{"field": "id", "operator": "in", "value": model_ids}],
    }
    model_search = config.MODELS_URI + config.MODELS_SEARCH_ENDPOINT
    response = make_request_with_retry(
        url=model_search, body=body, method="POST"
    )
    result = response.json()
    items = result.get("data")
    return {item.get("id"): item.get("type") for item in items}
