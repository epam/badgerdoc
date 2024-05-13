import logging
from typing import Dict, List, Union

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException

from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
    get_response,
)
from annotation.utils import get_service_uri

load_dotenv(find_dotenv())
JOBS_SERVICE_HOST = get_service_uri("JOBS_")
JOBS_SEARCH_URL = f"{JOBS_SERVICE_HOST}/jobs/search"
JOBS_FILE_ID_FIELD = "id"
JOBS_FILE_NAME_FIELD = "name"

logger = logging.getLogger(__name__)


class JobUpdateException(Exception):
    def __init__(self, exc_info: Union[str, RequestException]):
        self.exc_info = exc_info


def update_job_status(callback_url: str, status: str, tenant: str, token: str):
    try:
        job_response = requests.put(
            callback_url,
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json={
                "status": status,
            },
            timeout=5,
        )
        if job_response.status_code != 200:
            raise JobUpdateException(job_response.text)
    except RequestException as exc:
        raise JobUpdateException(exc)


def append_job_categories(
    job_id: str, categories: List[str], tenant: str, token: str
) -> None:
    logger.info("Append categories %s to job %s", categories, job_id)
    try:
        job_response = requests.put(
            f"{JOBS_SERVICE_HOST}/jobs/{job_id}",
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json={
                "categories_append": categories,
            },
            timeout=5,
        )
        if job_response.status_code != 200:
            raise JobUpdateException(job_response.text)
    except RequestException as exc:
        raise JobUpdateException(exc)


def get_job_names(
    job_ids: List[int], tenant: str, token: str
) -> Dict[int, str]:
    """
    Return dict of job_id and its name for provided
    job_ids from jobs microservice.
    """
    jobs = get_response(
        JOBS_FILE_ID_FIELD, job_ids, JOBS_SEARCH_URL, tenant, token
    )
    return {j[JOBS_FILE_ID_FIELD]: j[JOBS_FILE_NAME_FIELD] for j in jobs}
