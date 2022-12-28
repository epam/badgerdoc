import os
from typing import List, Union

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException
from app.models import ManualAnnotationTask

load_dotenv(find_dotenv())
USERS_SEARCH_URL = os.environ.get("USERS_SEARCH_URL")


class GetUserInfoException(Exception):
    def __init__(self, exc_info: Union[str, RequestException]):
        self.exc_info = exc_info


def get_response(callback_url: str, user_id: str, tenant: str, token: str):
    try:
        user_response = requests.get(
            f"{callback_url}/{user_id}",
            headers={
                "X-Current-Tenant": tenant,
                "Authorization": f"Bearer {token}",
            },
            timeout=5,
        )
        if user_response.status_code != 200:
            raise GetUserInfoException(user_response.text)
        return user_response.json().get("username")
    except RequestException as exc:
        raise GetUserInfoException(exc)


def get_user_logins(
    tasks: List[ManualAnnotationTask], tenant: str, token: str
) -> dict[str:str]:
    """
    Return list of logins for provided tasks from users microservice.
    """
    user_ids = [_.user_id for _ in tasks]
    return {
        str(user_id): get_response(USERS_SEARCH_URL, user_id, tenant, token)
        for user_id in user_ids
    }
