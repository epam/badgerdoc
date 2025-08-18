from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from helpers.base_client.base_client import BaseClient


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    id_token: Optional[str] = None
    scope: Optional[str] = None
    session_state: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None


class AuthService:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    def get_token(
        self, username: str, password: str, client_id: str = "admin-cli"
    ) -> tuple[str, str]:
        resp = self.client.post(
            "/users/token",
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "client_id": client_id,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        result = TokenResponse.model_validate(resp.json())
        return result.access_token, result.refresh_token

    def refresh_token(
        self, refresh_token: str, client_id: str = "admin-cli"
    ) -> tuple[str, str]:
        resp = self.client.post(
            "/users/refresh_token",
            json={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": refresh_token,
            },
        )
        result = TokenResponse.model_validate(resp.json())
        return result.access_token, result.refresh_token
