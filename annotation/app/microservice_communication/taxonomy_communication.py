import os
from typing import Union, Optional

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
    taxonomy_version: Optional[int] = None,
):
    response_budy = {
        "category_id": category_id,
        "taxonomy_id": taxonomy_id,
    }
    if taxonomy_version is not None:
        response_budy["taxonomy_version"] = taxonomy_version
    try:
        response = requests.post(
            "{url}/link_category".format(
                url=TAXONOMY_URL, taxonomy_id=taxonomy_id
            ),
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            json=response_budy,
            timeout=5,
        )
        if response.status_code != 201:
            raise TaxonomyLinkException(response.text)
    except RequestException as exc:
        raise TaxonomyLinkException(exc)
