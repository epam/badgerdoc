from typing import List

import requests
from fastapi import Depends
from fastapi import Header
from fastapi import UploadFile
from requests import RequestException
from requests import Timeout
from tenant_dependency import TenantData

from src.config import settings
from src.utils.common_utils import raise_request_exception


def upload_files(
        files: List[UploadFile],
        token: TenantData = Depends,
        current_tenant: str = Header(None, alias="X-Current-Tenant"),
):

    assets_url = settings.assets_service_url
    files_body = {"files": (fl.filename, fl.file) for fl in files}
    response = None
    try:
        response = requests.post(
            url=assets_url,
            headers={
                "X-Current-Tenant": current_tenant,
                "Authorization": f"Bearer {token.token}",
            },
            timeout=5,
            files=files_body
        )
    except (ConnectionError, RequestException, Timeout) as err:
        raise_request_exception(err)
    if response.status_code != 200:
        raise_request_exception(response.text)
    return response
