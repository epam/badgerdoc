import os
from typing import List

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException

from app.errors import TaxonomyLinkException
from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)

load_dotenv(find_dotenv())
TAXONOMY_URL = os.environ.get("TAXONOMY_URL")


def send_category_taxonomy_link(
    category_id: str,
    tenant: str,
    token: str,
    taxonomy_link_params: List[dict],
):
    request_body = [
        {"category_id": category_id, **param} for param in taxonomy_link_params
    ]
    try:
        response = requests.post(
            "{url}/link_category".format(url=TAXONOMY_URL),
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json=request_body,
            timeout=5,
        )
        if response.status_code != 201:
            raise TaxonomyLinkException(response.json()["detail"])
    except RequestException as exc:
        raise TaxonomyLinkException(exc)


def delete_taxonomy_link(
    category_id: str,
    tenant: str,
    token: str,
):
    try:
        response = requests.delete(
            f"{TAXONOMY_URL}/link_category/{category_id}",
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            timeout=5,
        )
        if response.status_code != 204:
            raise TaxonomyLinkException(response.json()["detail"])
    except RequestException as exc:
        raise TaxonomyLinkException(exc)
