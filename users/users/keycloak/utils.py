import asyncio
from typing import Dict, Union

import aiohttp
from users import config
from users.keycloak import query, schemas
from users.logger import Logger
from users.schemas import Users

realm = config.KEYCLOAK_REALM


def create_filters(users: Users) -> Dict[str, Union[str, None]]:
    return (
        {item.field: item.value for item in users.filters}  # type: ignore
        if users.filters is not None
        else {}
    )


async def get_username(
    access_token: schemas.ClientViewsUsersAccessToken, user_id: str
):
    for _ in range(2):
        try:
            return await query.get_user(realm, access_token.token, user_id)
        except aiohttp.ClientResponseError as e:
            if e.status in {401, 403}:
                Logger.info(
                    "Access Token for ClientViewsAllUsers_Role is expired. "
                    "Creating new one"
                )
                await access_token.request_new_token()
                await asyncio.sleep(1)
            else:
                raise e
