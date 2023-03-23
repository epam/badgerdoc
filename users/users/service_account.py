import logging
import os
from datetime import datetime

import jwt

from users.keycloak import query

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


class AuthToken:
    def __init__(self) -> None:
        self._token = ""

    async def get_token(self) -> str:
        if not self._token or self.is_expired():
            logger.debug("Requesting new token")
            auth_data = await query.get_master_realm_auth_data()
            self._token = auth_data.get("access_token")
        return self._token

    def is_expired(self) -> bool:
        exp = jwt.decode(
            self._token,
            algorithms=["RS256", "HS256"],
            options={"verify_signature": False},
        ).get("exp")
        return datetime.utcnow().timestamp() >= exp


auth_token = AuthToken()
