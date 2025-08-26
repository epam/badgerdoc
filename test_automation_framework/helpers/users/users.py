from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from helpers.base_client.base_client import BaseClient


class UserAccess(BaseModel):
    manageGroupMembership: bool
    view: bool
    mapRoles: bool
    impersonate: bool
    manage: bool


class UserResponse(BaseModel):
    id: str
    username: str
    enabled: bool
    email: Optional[str] = None
    emailVerified: Optional[bool] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    access: Optional[UserAccess] = None


class UsersClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def search_users(self, filters: Optional[List[Dict[str, Any]]] = None) -> List[UserResponse]:
        payload = {"filters": filters or []}
        resp = self.post_json(
            "/users/users/search", json=payload, headers=self._default_headers(content_type_json=True)
        )
        return [UserResponse.model_validate(u) for u in resp]
