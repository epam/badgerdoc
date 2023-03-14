import asyncio
from typing import Dict, Union

import aiohttp
import src.config as conf
import src.keycloak.query as kc_query
import src.keycloak.schemas as kc_schemas
from src.logger import Logger
from src.schemas import Users

realm = conf.KEYCLOAK_REALM


def create_filters(users: Users) -> Dict[str, Union[str, None]]:
    return (
        {item.field: item.value for item in users.filters}  # type: ignore
        if users.filters is not None
        else {}
    )


async def get_username(
    access_token: kc_schemas.ClientViewsUsersAccessToken, user_id: str
):
    for _ in range(2):
        try:
            return await kc_query.get_user(realm, access_token.token, user_id)
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
