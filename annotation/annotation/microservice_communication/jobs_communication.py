import logging
from typing import Dict, List, Union

from aiohttp import ClientError, ClientSession, ClientTimeout
from dotenv import find_dotenv, load_dotenv

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
    def __init__(self, exc_info: Union[str, ClientError]):
        self.exc_info = exc_info


async def update_job_status(
    callback_url: str, status: str, tenant: str, token: str
):
    headers = {
        HEADER_TENANT: tenant,
        AUTHORIZATION: f"{BEARER} {token}",
    }
    json_data = {"status": status}
    timeout = ClientTimeout(total=5)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.put(
                callback_url, headers=headers, json=json_data
            ) as response:
                if response.status != 200:
                    raise JobUpdateException(await response.text())
        except ClientError as exc:
            raise JobUpdateException(exc)


async def append_job_categories(
    job_id: str, categories: List[str], tenant: str, token: str
):
    logger.info(f"Append categories {categories} to job {job_id}")
    url = f"{JOBS_SERVICE_HOST}/jobs/{job_id}"
    headers = {
        HEADER_TENANT: tenant,
        AUTHORIZATION: f"{BEARER} {token}",
    }
    json_data = {"categories_append": categories}
    timeout = ClientTimeout(total=5)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.put(
                url, headers=headers, json=json_data
            ) as response:
                if response.status != 200:
                    raise JobUpdateException(await response.text())
        except ClientError as exc:
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
