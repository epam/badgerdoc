from typing import Dict, Union

from users import config
from users.schemas import Users

realm = config.KEYCLOAK_REALM


def create_filters(users: Users) -> Dict[str, Union[str, None]]:
    return (
        {item.field: item.value for item in users.filters}  # type: ignore
        if users.filters is not None
        else {}
    )
