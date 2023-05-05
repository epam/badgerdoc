import os
from typing import Dict, List, Union

import requests
from dotenv import find_dotenv, load_dotenv
from requests import RequestException

from annotation.logger import Logger

load_dotenv(find_dotenv())
USERS_GET_USER_URL = os.environ.get("USERS_GET_USER_URL")


class GetUserInfoException(Exception):
    def __init__(self, exc_info: Union[str, RequestException]):
        self.exc_info = exc_info


class GetUserInfoAccessDenied(GetUserInfoException):
    pass


def get_username(callback_url: str, user_id: str, tenant: str, token: str):
    try:
        user_response = requests.get(
            f"{callback_url}/{user_id}",
            headers={
                "X-Current-Tenant": tenant,
                "Authorization": f"Bearer {token}",
            },
            timeout=5,
        )
        if user_response.status_code == 403:
            raise GetUserInfoAccessDenied(
                "Access Denied on request to users microservice "
            )
        if user_response.status_code == 404:
            Logger.info("User %s is not found in 'users'", user_id)
            return ""
        if user_response.status_code != 200:
            raise GetUserInfoException(
                f"Failed request to 'users' microservice: {user_response.text}"
            )
        return user_response.json().get("username")
    except RequestException as exc:
        raise GetUserInfoException(exc)


def get_user_names(
    user_ids: List[str], tenant: str, token: str
) -> Dict[str, str]:
    """
    Return list of logins for provided tasks from users microservice.
    """
    return {
        str(user_id): get_username(USERS_GET_USER_URL, user_id, tenant, token)
        for user_id in user_ids
    }
