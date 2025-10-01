import datetime
import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

import veeva.models.orm as orm

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(stdout_handler)


class VeevaPmAuthError(Exception):
    """Custom exception for Veeva PM authentication errors."""

    pass


@dataclass
class VeevaPmVault:
    id: int
    name: str
    url: str


@dataclass
class VeevaPmSession:
    session_id: str
    response_status: str
    user_id: int
    vault_id: int
    vault_ids: list[VeevaPmVault]


def map_response_to_session(
    response_data: dict,
) -> VeevaPmSession:
    """
    Map the authentication response data to a VeevaPmSession object.

    Args:
        response_data: The JSON response data from the authentication request

    Returns:
        VeevaPmSession: An instance of VeevaPmSession populated with the response data
    """
    vaults = [
        VeevaPmVault(
            id=vault["id"],
            name=vault["name"],
            url=vault["url"],
        )
        for vault in response_data.get("vaultIds", [])
    ]

    return VeevaPmSession(
        session_id=response_data["sessionId"],
        response_status=response_data["responseStatus"],
        user_id=response_data["userId"],
        vault_id=response_data["vaultId"],
        vault_ids=vaults,
    )


async def auth(synchronization: orm.Synchronization) -> dict:
    """
    Authenticate the synchronization job with Veeva PM.

    This function performs authentication for the synchronization job,
    ensuring that the necessary credentials are valid and can be used
    to access Veeva PM resources.

    Args:
        synchronization: The Synchronization object containing configuration details

    Returns:
        dict: The authentication response containing session ID and other details
    """
    logger.info("Authenticating with Veeva PM")

    auth_url = f"{synchronization.configuration.veeva_pm_host}/api/v25.1/auth"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    data = {
        "username": synchronization.configuration.veeva_pm_login,
        "password": synchronization.configuration.veeva_pm_password,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                auth_url, headers=headers, data=data
            ) as response:
                response_data = await response.json()

                if response_data.get("responseStatus") != "SUCCESS":
                    error_msg = f"Authentication failed: {response.status} - {response_data.get('responseMessage', 'Unknown error')}"
                    logger.error(error_msg)
                    raise VeevaPmAuthError(error_msg)

                logger.info("Authentication successful")
                return response_data

        except aiohttp.ClientError as e:
            error_msg = f"Connection error during authentication: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)


async def get_delta(
    veeva_pm_session: VeevaPmSession,
    version_modified_date_from: Optional[datetime.datetime] = None,
) -> dict:
    pass


async def run(
    session: AsyncSession,
    synchronization: orm.Synchronization,
) -> None:
    """
    Run the synchronization process for the given synchronization job.

    This function executes the synchronization logic for the specified synchronization job,
    updating its status and handling any errors that may occur.

    Args:
        session: The async SQLAlchemy session for database operations
        synchronization: The Synchronization object to run

    Returns:
        Synchronization: The updated Synchronization object after running the job
    """
    logger.info("Running synchronization job: %s", synchronization)
    logger.info("Configuration: %s", synchronization.configuration)
    logger.info(
        "Veeva PM host: %s", synchronization.configuration.veeva_pm_host
    )
    logger.info(
        "Veeva PM login: %s", synchronization.configuration.veeva_pm_login
    )
    logger.info(
        "Veeva PM password: %s",
        synchronization.configuration.veeva_pm_password,
    )
    logger.info("Veeva PM VQL: %s", synchronization.configuration.veeva_pm_vql)
