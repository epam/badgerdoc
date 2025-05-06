from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def camelize(string: str) -> str:
    """Transform snake_case to camelCase."""
    first, *others = string.lstrip("_").split("_")
    return "".join([first.lower(), *map(str.title, others)])


class UserConsent(BaseModel):
    """UserConsentRepresentation."""

    client_id: Optional[str] = None
    created_date: Optional[int] = None
    granted_client_scopes: Optional[List[str]] = None
    last_update_date: Optional[int] = None
    model_config = ConfigDict(alias_generator=camelize, str_strip_whitespace=True, populate_by_name=True)


class Credential(BaseModel):
    """CredentialRepresentation."""

    created_date: Optional[int] = None
    credential_data: Optional[str] = None
    id: Optional[str] = None
    priority: Optional[int] = None
    secret_data: Optional[str] = None
    temporary: Optional[bool] = None
    type: Optional[str] = None
    user_label: Optional[str] = None
    value: Optional[str] = None
    model_config = ConfigDict(alias_generator=camelize, str_strip_whitespace=True, populate_by_name=True)


class FederatedIdentity(BaseModel):
    """FederatedIdentityRepresentation."""

    identity_provider: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    model_config = ConfigDict(alias_generator=camelize, str_strip_whitespace=True, populate_by_name=True)


class User(BaseModel):
    """UserRepresentation."""

    access: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None
    client_consents: Optional[List[UserConsent]] = None
    client_roles: Optional[Dict[str, Any]] = None
    created_timestamp: Optional[int] = None
    credentials: Optional[List[Credential]] = None
    disableable_credential_types: Optional[List[str]] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    enabled: Optional[bool] = None
    federated_identities: Optional[List[FederatedIdentity]] = None
    federation_link: Optional[str] = None
    first_name: Optional[str] = None
    groups: Optional[List[str]] = None
    id: Optional[str] = None
    last_name: Optional[str] = None
    not_before: Optional[int] = None
    origin: Optional[str] = None
    realm_roles: Optional[List[str]] = None
    required_actions: Optional[List[str]] = None
    self: Optional[str] = None
    service_account_client_id: Optional[str] = None
    username: Optional[str] = None
    # TODO[pydantic]: The following keys were removed: `underscore_attrs_are_private`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(alias_generator=camelize, str_strip_whitespace=True, populate_by_name=True, underscore_attrs_are_private=True)

    @staticmethod
    def filter_users(
        users: List[User],
        user_name_substring: Union[str, None] = None,
        user_id: List[Union[str, None]] = None,
    ) -> List[User]:
        """Filter users"""

        filtered_users_name = []
        filtered_users_id = []

        if user_name_substring is None:
            filtered_users_name = users
        else:
            for user in users:
                if user_name_substring in user.username:
                    filtered_users_name.append(user)

        if user_id is None:
            filtered_users_id = filtered_users_name
        else:
            for user in filtered_users_name:
                if user.id in user_id:
                    filtered_users_id.append(user)

        return filtered_users_id

    def add_tenant(self, tenant: str) -> None:
        """Add tenant to user's attribute 'tenants'."""
        tenants_key = "tenants"
        if self.attributes is None or self.attributes.get(tenants_key) is None:
            self.attributes = {tenants_key: []}
        if tenant not in self.attributes[tenants_key]:
            self.attributes[tenants_key].append(tenant)

    def remove_tenant(self, tenant: str) -> None:
        """Remove tenant from user's attribute 'tenants'."""
        tenants_key = "tenants"
        if self.attributes:
            user_tenants = self.attributes.get(tenants_key, [])
            if tenant in user_tenants:
                user_tenants.remove(tenant)


class Group(BaseModel):
    """GroupRepresentation."""

    access: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None
    clientRoles: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None
    realm_roles: Optional[List[str]] = None
    sub_groups: Optional[List[Group]] = None
    model_config = ConfigDict(alias_generator=camelize, str_strip_whitespace=True, populate_by_name=True)


Group.update_forward_refs()


class AddressClaimSet(BaseModel):
    """AddressClaimSet."""

    country: Optional[str] = None
    formatted: Optional[str] = None
    locality: Optional[str] = None
    postal_code: Optional[str] = None
    region: Optional[str] = None
    street_address: Optional[str] = None
    model_config = ConfigDict(str_strip_whitespace=True)


class Permission(BaseModel):
    """Permission."""

    claims: Optional[Dict[str, Any]] = None
    rsid: Optional[str] = None
    rsname: Optional[str] = None
    scopes: Optional[List[str]] = None
    model_config = ConfigDict(str_strip_whitespace=True)


class AccessTokenAuthorization(BaseModel):
    """AccessToken-Authorization."""

    permissions: Optional[List[Permission]] = None


class AccessTokenCategory(str, Enum):
    INTERNAL = "INTERNAL"
    ACCESS = "ACCESS"
    ID = "ID"
    ADMIN = "ADMIN"
    USERINFO = "USERINFO"
    LOGOUT = "LOGOUT"
    AUTHORIZATION_RESPONSE = "AUTHORIZATION_RESPONSE"


class AccessTokenAccess(BaseModel):
    """AccessToken-Access."""

    roles: Optional[List[str]] = None
    verify_caller: Optional[bool] = None
    model_config = ConfigDict(str_strip_whitespace=True)


class AccessToken(BaseModel):
    """AccessToken."""

    acr: Optional[str] = None
    address: Optional[AddressClaimSet] = None
    allowed_origins: Optional[List[str]] = Field(None, alias="allowed-origins")
    at_hash: Optional[str] = None
    auth_time: Optional[int] = None
    authorization: Optional[AccessTokenAuthorization] = None
    azp: Optional[str] = None
    birthdate: Optional[str] = None
    c_hash: Optional[str] = None
    category: Optional[AccessTokenCategory] = None
    claims_locales: Optional[str] = None
    cnf: Optional[str] = Field(None, alias="x5t#S256")
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    exp: Optional[int] = None
    family_name: Optional[str] = None
    gender: Optional[str] = None
    given_name: Optional[str] = None
    iat: Optional[int] = None
    iss: Optional[str] = None
    jti: Optional[str] = None
    locale: Optional[str] = None
    middle_name: Optional[str] = None
    name: Optional[str] = None
    nbf: Optional[int] = None
    nickname: Optional[str] = None
    nonce: Optional[str] = None
    other_claims: Optional[Dict[str, Any]] = Field(None, alias="otherClaims")
    phone_number: Optional[str] = None
    phone_number_verified: Optional[bool] = None
    picture: Optional[str] = None
    preferred_username: Optional[str] = None
    profile: Optional[str] = None
    realm_access: Optional[AccessTokenAccess] = None
    s_hash: Optional[str] = None
    scope: Optional[str] = None
    session_state: Optional[str] = None
    sid: Optional[str] = None
    sub: Optional[str] = None
    tenants: Optional[List[str]] = None
    trusted_certs: Optional[List[str]] = Field(None, alias="trusted-certs")
    typ: Optional[str] = None
    updated_at: Optional[int] = None
    website: Optional[str] = None
    zoneinfo: Optional[str] = None
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)


class TokenResponse(BaseModel):
    """Represent Keycloak token response."""

    access_token: str
    expires_in: Optional[int] = None
    refresh_expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    token_type: str
    id_token: Optional[str] = None
    not_before_policy: Optional[int] = Field(None, alias="not-before-policy")
    session_state: Optional[str] = None
    scope: Optional[str] = None
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)


class OAuthRequest(BaseModel):
    """Base class for authorization requests"""

    client_id: Optional[str] = None
    grant_type: str
    client_secret: Optional[str] = None


class TokenRequest(OAuthRequest):
    """Represent Keycloak token request."""

    username: str
    password: str
    grant_type: str = "password"
    scope: Optional[str] = None
    model_config = ConfigDict(str_strip_whitespace=True)

    @staticmethod
    def from_fastapi_form(
        request_form: OAuth2PasswordRequestForm,
    ) -> TokenRequest:
        """Create model from FastAPI OAuth2 Request Form."""
        scope = request_form.scopes[0] if request_form.scopes else None
        return TokenRequest(
            username=request_form.username,
            password=request_form.password,
            client_id=request_form.client_id,
            grant_type=request_form.grant_type,
            client_secret=request_form.client_secret,
            scope=scope,
        )


class RefreshTokenRequest(OAuthRequest):
    """Represents Keycloak token refreshment request"""

    client_id: str = "admin-cli"
    grant_type: str = "refresh_token"
    refresh_token: str
