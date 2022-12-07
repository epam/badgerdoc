from typing import Any, Dict, List, TypedDict, Union

import aiohttp
import src.config as config
import src.keycloak.resources as resources
import src.keycloak.schemas as schemas
from fastapi import HTTPException, status
from src import logger


class AuthData(TypedDict):
    """TypedDict to check Auth Data"""

    access_token: str


class Token_Data(TypedDict):
    """TypedDict to check Token Data"""

    name: str
    given_name: str
    family_name: str
    preferred_username: str
    email: str
    tenants: List[str]
    username: str
    active: bool


class IDP_Data(TypedDict):
    """TypedDict to check Identity Providers Data"""

    alias: str


def create_bearer_header(token: str) -> Dict[str, str]:
    """Create dictionary-header with the given token."""
    return {"Authorization": f"Bearer {token}"}


async def create_user(
    token: str, realm: str, username: str, email: str
) -> None:
    """Create user"""
    url = resources.users_uri.substitute(realm=realm)
    method = "POST"
    headers = create_bearer_header(token)
    payload = {"username": username, "email": email, "enabled": True}
    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        raise_for_status=True,
    ):
        return


async def get_users_by_role(
    token: str, realm: str, role: str
) -> List[schemas.User]:
    """Get list of users from keycloak by role"""

    url = resources.users_by_role_uri.substitute(realm=realm, role=role)
    method = "GET"
    headers = create_bearer_header(token)

    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        raise_for_status=True,
    ) as resp:
        return [schemas.User.parse_obj(user) for user in await resp.json()]


async def get_token_v2(
    realm: str, request_form: Union[schemas.TokenRequest, schemas.RefreshTokenRequest]
) -> schemas.TokenResponse:
    """Get access token.

    :param realm: Realm to get token for.
    :param request_form: Request form with credentials.
    :return: Token for the user.
    """
    url = resources.token_uri.substitute(realm=realm)
    method = "POST"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = request_form.dict(exclude_none=True)
    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        data=payload,
        raise_for_status=True,
    ) as resp:
        return schemas.TokenResponse.parse_obj(await resp.json())


async def get_users_v2(
    realm: str, token: str, **filters: Any
) -> List[schemas.User]:
    """Get users from realm, filtered according to filters.

    :param realm: Keycloak realm.
    :param token: Admin token.
    :param filters: Filters.
    :return: Found users.
    """
    url = resources.users_uri.substitute(realm=realm)
    method = "GET"
    headers = create_bearer_header(token)
    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        params=filters,
        raise_for_status=True,
    ) as resp:
        return [schemas.User.parse_obj(user) for user in await resp.json()]


async def get_user(realm: str, token: str, user_id: str) -> schemas.User:
    """Get representation of the user.

    :param realm: Keycloak realm.
    :param token: Admin token.
    :param user_id: User id to find.
    :return: Found user.
    """
    url = resources.user_uri.substitute(realm=realm, id=user_id)
    method = "GET"
    headers = create_bearer_header(token)
    logger.Logger.info(
        "Sending request to Keycloak url: %s to get user_info user_id: %s. "
        "Deprecating endpoint",
        url,
        user_id,
    )
    async with aiohttp.request(
        method=method, url=url, headers=headers, raise_for_status=True
    ) as resp:
        return schemas.User.parse_obj(await resp.json())


async def introspect_token(token: str) -> Token_Data:
    """Introspects token data by sending request to Keycloak REST API"""
    url = resources.token_introspection_uri.substitute(realm="master")
    method = "POST"
    headers = create_bearer_header(token)
    payload = {
        "token": token,
        "client_id": "BadgerDoc",
        "client_secret": config.BADGERDOC_CLIENT_SECRET,
    }
    logger.Logger.info(
        "Sending request to Keycloak url: %s to get user_info",
        url,
    )
    try:
        async with aiohttp.request(
            method=method,
            url=url,
            headers=headers,
            raise_for_status=True,
            data=payload,
        ) as resp:
            data = await resp.json()
            data_to_return: Token_Data = (
                data  # casting into TypedDict for linter checks
            )
            return data_to_return
    except aiohttp.ClientConnectionError as e:
        logger.Logger.error("Exception while sending request to Keycloak: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Exception while sending request to Keycloak: {e}",
        )


async def get_groups(
    realm: str, token: str, name: str = None
) -> List[schemas.Group]:
    """Get group from realm by its name.

    :param realm: Keycloak realm.
    :param token: Admin token.
    :param name: Name of groups to find.
    :return: Found groups.
    :raise aiohttp.HTTPNotFound: Group not found.
    """
    url = resources.groups_uri.substitute(realm=realm)
    method = "GET"
    headers = create_bearer_header(token)
    params = {"search": name} if name else None
    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        raise_for_status=True,
    ) as resp:
        return [schemas.Group.parse_obj(group) for group in await resp.json()]


async def create_group(realm: str, token: str, group: schemas.Group) -> None:
    """Create new group.

    :param realm: Keycloak group.
    :param token: Admin token.
    :param group: Group to create.
    """
    url = resources.groups_uri.substitute(realm=realm)
    method = "POST"
    headers = create_bearer_header(token)
    payload = group.dict(exclude_none=True)
    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        raise_for_status=True,
    ):
        return


async def update_user(
    realm: str, token: str, user_id: str, upd: schemas.User
) -> None:
    """Update user.

    :param realm: Keycloak realm.
    :param token: Admin token.
    :param user_id: User id to update.
    :param upd: What to update.
    """
    url = resources.user_uri.substitute(realm=realm, id=user_id)
    method = "PUT"
    headers = create_bearer_header(token)
    payload = upd.dict(by_alias=True, exclude_none=True)
    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        raise_for_status=True,
    ):
        return


async def execute_action_email(token: str, realm: str, user_id: str) -> None:
    """Send email to user for updating user profile"""
    url = resources.execute_actions_email_uri.substitute(
        realm=realm, id=user_id
    )
    method = "PUT"
    headers = create_bearer_header(token)
    payload = ["UPDATE_PROFILE", "UPDATE_PASSWORD"]
    async with aiohttp.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        raise_for_status=True,
    ):
        return


async def get_master_realm_auth_data() -> AuthData:
    """Gets authentication data (including access token) for admin role"""
    payload = {
        "username": "admin",
        "password": "admin",
        "client_id": "master-realm",
        "client_secret": config.ADMIN_CLIENT_SECRET,
        "grant_type": "password",
    }
    url = resources.token_uri.substitute(realm="master")
    logger.Logger.info(
        "Sending request to Keycloak url: %s to get admin auth data, " "payload: %s",
        url,
        payload,
    )
    try:
        async with aiohttp.request(
            method="POST",
            url=url,
            raise_for_status=True,
            data=payload,
        ) as resp:
            data = await resp.json()
            data_to_return: AuthData = (
                data  # casting into TypedDict for linter checks
            )
            return data_to_return

    except aiohttp.ClientConnectionError as e:
        logger.Logger.error("Exception while sending request to Keycloak: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Exception while sending request to Keycloak: {e}",
        )


async def get_identity_providers_data(
    master_realm_access_token: str,
) -> Any:
    """Get all data about Identity Providers set in Keycloak"""
    headers = {"Authorization": f"Bearer {master_realm_access_token}"}
    url = resources.identity_providers_uri.substitute(realm="master")
    logger.Logger.info(
        "Sending request to Keycloak url: %s to get identity providers data",
        url,
    )
    try:
        async with aiohttp.request(
            method="GET",
            url=url,
            headers=headers,
            raise_for_status=True,
        ) as resp:
            return await resp.json()

    except aiohttp.ClientConnectionError as e:
        logger.Logger.error("Exception while sending request to Keycloak: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Exception while sending request to Keycloak: {e}",
        )
