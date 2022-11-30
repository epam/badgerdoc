import os
from typing import Optional, Union

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException

from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)

load_dotenv(find_dotenv())
TAXONOMY_URL = os.environ.get("TAXONOMY_URL")


class TaxonomyLinkException(Exception):
    def __init__(self, exc_info: Union[str, RequestException]):
        self.exc_info = exc_info


def link_job_with_taxonomy(
    job_id: str,
    taxonomy_id: str,
    tenant: str,
    token: str,
    taxonomy_version: Optional[int] = None,
) -> None:
    request_body = {
        "job_id": job_id,
        "taxonomy_id": taxonomy_id,
    }
    if taxonomy_version is not None:
        request_body["taxonomy_version"] = taxonomy_version
    url = "{url}/link_job".format(url=TAXONOMY_URL)
    return _request_taxonomy_service(
        tenant=tenant, token=token, request_body=request_body, url=url
    )


def link_category_with_taxonomy(
    category_id: str,
    taxonomy_id: str,
    tenant: str,
    token: str,
    taxonomy_version: Optional[int] = None,
) -> None:
    request_body = {
        "category_id": category_id,
        "taxonomy_id": taxonomy_id,
    }
    if taxonomy_version is not None:
        request_body["taxonomy_version"] = taxonomy_version
    url = "{url}/link_category".format(url=TAXONOMY_URL)
    return _request_taxonomy_service(
        tenant=tenant, token=token, request_body=request_body, url=url
    )


def _request_taxonomy_service(
    tenant: str,
    token: str,
    url: str,
    request_body: dict,
) -> None:
    try:
        response = requests.post(
            url,
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json=request_body,
            timeout=5,
        )
        if response.status_code != 201:
            raise TaxonomyLinkException(response.text)
    except RequestException as exc:
        raise TaxonomyLinkException(exc)
