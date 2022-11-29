import os
from typing import Union

import requests
from dotenv import load_dotenv, find_dotenv
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


def link_category_with_taxonomy(
    category_id: str,
    taxonomy_id: str,
    tenant: str,
    token: str,
):
    try:
        response = requests.post(
            "{url}/taxonomy/{taxonomy_id}/link_category".format(
                url=TAXONOMY_URL, taxonomy_id=taxonomy_id
            ),
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json={
                "category_id": category_id,
            },
            timeout=5,
        )
        if response.status_code != 201:
            raise TaxonomyLinkException(response.text)
    except RequestException as exc:
        raise TaxonomyLinkException(exc)
