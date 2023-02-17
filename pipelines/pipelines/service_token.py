import json
from typing import Optional

from pipelines import config, http_utils
from pipelines.log import get_logger

ACCESS_TOKEN = "access_token"

POST = "POST"

CLIENT_CREDENTIALS = "client_credentials"

PIPELINES = "pipelines"

WWW_FORM_URLENCODED = "application/x-www-form-urlencoded"

logger = get_logger(__file__)


def get_service_token() -> Optional[str]:
    """Creates Pipelines client token"""
    token = None
    url = config.KEYCLOAK_TOKEN_URI
    headers = {"Content-Type": WWW_FORM_URLENCODED}
    payload = {
        "client_id": PIPELINES,
        "client_secret": config.CLIENT_SECRET,
        "grant_type": CLIENT_CREDENTIALS,
    }
    response = http_utils.make_request_with_retry(
        method="POST", url=url, data=payload, headers=headers
    )
    try:
        response_json = response.json()
    except json.JSONDecodeError:
        logger.exception(f"Response {response} from {url} cannot be converted to json.")
    try:
        token = response_json[ACCESS_TOKEN]
    except AttributeError:
        logger.exception(f"Unable to extract token from response {response} from {url}")

    return token
