from typing import Any, Dict, List, Optional, Union

import users.keycloak.schemas as schemas
from users.schemas import Users


def create_filters(users: Users) -> Dict[str, Union[str, None]]:
    return (
        {item.field: item.value for item in users.filters}  # type: ignore
        if users.filters is not None
        else {}
    )
