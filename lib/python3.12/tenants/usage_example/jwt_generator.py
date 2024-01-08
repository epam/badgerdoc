from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional, Union

import jwt

SECRET = "some_secret_key"


def create_access_token(
    data: Dict[str, Any],
    secret: Union[str, bytes],
    expires_delta: Optional[int] = None,
    algorithm: str = "HS256",
) -> Any:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt


access_token = create_access_token(
    data={
        "sub": "901",
        "realm_access": {"roles": ["role-annotator"]},
        "tenants": ["tenant1", "epam"],
    },
    secret=SECRET,
    expires_delta=15,
    algorithm="HS256",
)
print(access_token)
