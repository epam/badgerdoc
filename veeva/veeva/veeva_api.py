import logging
import os
from typing import Any, Dict

import aiohttp

# Get base URL from environment variable
VEEVA_VAULT_HOST = os.environ.get("VEEVA_VAULT_HOST")

VEEVA_VAULT_USERNAME = os.environ.get("VEEVA_VAULT_USERNAME")
VEEVA_VAULT_PASSWORD = os.environ.get("VEEVA_VAULT_PASSWORD")

# todo: add stream handler for logging
logger = logging.getLogger("uvicorn")
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG").upper())


class VeevaAuthError(Exception):
    """Exception raised for Veeva PM authentication errors."""

    pass


async def auth(username: str, password: str) -> str:
    """
    Authenticate with Veeva PM and retrieve a session ID.

    Args:
        username: Veeva username
        password: Veeva password

    Returns:
        Session ID string if authentication is successful

    Raises:
        VeevaAuthError: If authentication fails for any reason
    """
    login_url = f"{VEEVA_VAULT_HOST}/api/v25.1/auth"

    payload = {"username": username, "password": password}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    logger.debug(
        "Attempting to authenticate with Veeva PM, username: %s", username
    )
    try:
        async with aiohttp.ClientSession() as session:
            # Use data parameter instead of json for form-encoded data
            async with session.post(
                login_url, data=payload, headers=headers
            ) as response:
                logger.debug("Got response from Veeva PM: %s", response.status)
                if response.status == 200:
                    response_data: Dict[str, Any] = await response.json()

                    logger.debug(
                        "Response data from Veeva PM: %s", response_data
                    )
                    # Veeva typically returns the session ID in the response
                    # Adjust the key based on actual Veeva PM API response structure
                    session_id = response_data.get("sessionId")

                    if session_id:
                        logger.info("Successfully authenticated with Veeva PM")
                        return session_id
                    else:
                        logger.error(
                            "Veeva returned error type: %s. Change to DEBUG level "
                            "to see full response.",
                            response_data.get("errorType"),
                        )
                        raise VeevaAuthError(
                            "Session ID not found in response"
                        )
                else:
                    raise VeevaAuthError(
                        f"Authentication failed with status {response.status}"
                    )
    except aiohttp.ClientError as err:
        raise VeevaAuthError("Authentication connection error") from err
    except VeevaAuthError:
        raise
    except Exception as err:
        raise VeevaAuthError("Unexpected authentication error") from err
