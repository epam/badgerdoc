import os
from typing import Dict, List, Union

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException

from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
    get_response,
)

load_dotenv(find_dotenv())
JOBS_SEARCH_URL = os.environ.get("JOBS_SEARCH_URL")


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


def get_job_names(
    job_ids: List[int], tenant: str, token: str
) -> Dict[int, str]:
    """
    Return dict of job_id and its name for provided
    job_ids from jobs microservice.
    """
    jobs = get_response(job_ids, JOBS_SEARCH_URL, tenant, token)
    return {j["id"]: j["name"] for j in jobs}
