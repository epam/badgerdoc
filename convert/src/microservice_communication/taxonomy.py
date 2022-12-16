from typing import List
from typing import Union

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException
from tenant_dependency import TenantData

from src.config import settings

load_dotenv(find_dotenv())


class TaxonomyLinkException(Exception):
    def __init__(self, exc_info: Union[str, RequestException]):
        self.exc_info = exc_info


def link_categories(
    category_id: str,
    taxonomy_link_params: List[dict],
    token: TenantData,
    tenant: str
):
    request_body = [
        {"category_id": category_id, **param} for param in taxonomy_link_params
    ]
    try:
        response = requests.post(
            "{url}/link_to_job".format(url=settings.taxonomy_service_url),
            headers={
                "X-Current-Tenant": tenant,
                "Authorization": f"Bearer {token.token}",
            },
            json=request_body,
            timeout=5,
        )
        if response.status_code != 201:
            raise TaxonomyLinkException(response.json()["detail"])
    except RequestException as exc:
        raise TaxonomyLinkException(exc)

