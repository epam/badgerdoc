from typing import Union
from typing import List

import requests
from src.config import settings
from dotenv import find_dotenv, load_dotenv
from requests import RequestException

from tenant_dependency import TenantData

load_dotenv(find_dotenv())

EXPECTED_PROGRESS = "finished"


class JobCreateException(Exception):
    def __init__(self, exc_info: Union[str, RequestException]):
        self.exc_info = exc_info


def create_jobs(jobs: List, token: TenantData, tenant: str):
    job_responses = []
    for job in jobs:
        try:
            job_response = requests.post(
                settings.job_creation_url,
                headers={
                    "X-Current-Tenant": tenant,
                    "Authorization": f"Bearer {token.token}",
                },
                json=job,
                timeout=5,
            )
            if job_response.status_code != 200:
                raise JobCreateException(job_response.text)
            job_responses.append(job_response)
        except RequestException as exc:
            raise JobCreateException(exc)
    return job_responses


def wait_for_end(jobs: List, token: TenantData, tenant: str):
    while True:
        try:
            job_response = requests.post(
                settings.job_service_url,
                headers={
                    "X-Current-Tenant": tenant,
                    "Authorization": f"Bearer {token.token}",
                },
                json=jobs,
                timeout=5,
            )
            if job_response.status_code != 200:
                raise JobCreateException(job_response.text)
            results = job_response.json()
            statuses = [_.get('finished') for _ in results.values()]
            if set(statuses) == {1}:
                return
        except RequestException as exc:
            raise JobCreateException(exc)


def start_jobs(jobs: List, token: TenantData, tenant: str):
    start_job_responses = []
    for job in jobs:
        try:
            job_response = requests.post(
                f"{settings.job_service_url}/start/{job.get('id')}",
                headers={
                    "X-Current-Tenant": tenant,
                    "Authorization": f"Bearer {token.token}",
                },
                timeout=5,
            )
            if job_response.status_code != 200:
                raise JobCreateException(job_response.text)
            start_job_responses.append(job_response)
        except RequestException as exc:
            raise JobCreateException(exc)
    return start_job_responses
