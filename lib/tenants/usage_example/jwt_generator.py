from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt

SECRET = "some_secret_key"


def create_access_token(
    data: Dict[str, Any], secret: str, expires_delta: Optional[int] = None
) -> Any:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm="HS256")
    return encoded_jwt


access_token = create_access_token(
    data={
        "user_id": 901,
        "roles": ["admin", "ml engineer", "devops"],
        "tenant": "merck",
    },
    secret=SECRET,
    expires_delta=15,
)
print(access_token)
