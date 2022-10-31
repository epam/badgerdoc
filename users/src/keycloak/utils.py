from typing import Any, Dict, List, Optional, Union

import src.keycloak.schemas as schemas
from src.schemas import Users


def create_filters(users: Users) -> Dict[str, Union[str, None]]:
    return (
        {item.field: item.value for item in users.filters}  # type: ignore
        if users.filters is not None
        else {}
    )
