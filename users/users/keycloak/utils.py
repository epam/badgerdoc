from typing import Dict, Union

from users import config, service_account
from users.keycloak import query
from users.schemas import Users

realm = config.KEYCLOAK_REALM


def create_filters(users: Users) -> Dict[str, Union[str, None]]:
    return (
        {item.field: item.value for item in users.filters}  # type: ignore
        if users.filters is not None
        else {}
    )


async def get_username(user_id: str):
    token = await service_account.auth_token.get_token()
    return await query.get_user(realm, token, user_id)
