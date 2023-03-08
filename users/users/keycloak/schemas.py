from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

import users.config as conf
import users.keycloak.query as kc_query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field


def camelize(string: str) -> str:
    """Transform snake_case to camelCase."""
    first, *others = string.lstrip("_").split("_")
    return "".join([first.lower(), *map(str.title, others)])


class UserConsent(BaseModel):
    """UserConsentRepresentation."""

    client_id: Optional[str]
    created_date: Optional[int]
    granted_client_scopes: Optional[List[str]]
    last_update_date: Optional[int]

    class Config:
        alias_generator = camelize
        anystr_strip_whitespace = True
        allow_population_by_field_name = True


class Credential(BaseModel):
    """CredentialRepresentation."""

    created_date: Optional[int]
    credential_data: Optional[str]
    id: Optional[str]
    priority: Optional[int]
    secret_data: Optional[str]
    temporary: Optional[bool]
    type: Optional[str]
    user_label: Optional[str]
    value: Optional[str]

    class Config:
        alias_generator = camelize
        anystr_strip_whitespace = True
        allow_population_by_field_name = True


class FederatedIdentity(BaseModel):
    """FederatedIdentityRepresentation."""

    identity_provider: Optional[str]
    user_id: Optional[str]
    user_name: Optional[str]

    class Config:
        alias_generator = camelize
        anystr_strip_whitespace = True
        allow_population_by_field_name = True


class User(BaseModel):
    """UserRepresentation."""

    access: Optional[Dict[str, Any]]
    attributes: Optional[Dict[str, Any]]
    client_consents: Optional[List[UserConsent]]
    client_roles: Optional[Dict[str, Any]]
    created_timestamp: Optional[int]
    credentials: Optional[List[Credential]]
    disableable_credential_types: Optional[List[str]]
    email: Optional[str]
    email_verified: Optional[bool]
    enabled: Optional[bool]
    federated_identities: Optional[List[FederatedIdentity]]
    federation_link: Optional[str]
    first_name: Optional[str]
    groups: Optional[List[str]]
    id: Optional[str]
    last_name: Optional[str]
    not_before: Optional[int]
    origin: Optional[str]
    realm_roles: Optional[List[str]]
    required_actions: Optional[List[str]]
    self: Optional[str]
    service_account_client_id: Optional[str]
    username: Optional[str]

    class Config:
        alias_generator = camelize
        anystr_strip_whitespace = True
        allow_population_by_field_name = True
        underscore_attrs_are_private = True

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

    access: Optional[Dict[str, Any]]
    attributes: Optional[Dict[str, Any]]
    clientRoles: Optional[Dict[str, Any]]
    id: Optional[str]
    name: Optional[str]
    path: Optional[str]
    realm_roles: Optional[List[str]]
    sub_groups: Optional[List[Group]]

    class Config:
        alias_generator = camelize
        anystr_strip_whitespace = True
        allow_population_by_field_name = True


Group.update_forward_refs()


class AddressClaimSet(BaseModel):
    """AddressClaimSet."""

    country: Optional[str]
    formatted: Optional[str]
    locality: Optional[str]
    postal_code: Optional[str]
    region: Optional[str]
    street_address: Optional[str]

    class Config:
        anystr_strip_whitespace = True


class Permission(BaseModel):
    """Permission."""

    claims: Optional[Dict[str, Any]]
    rsid: Optional[str]
    rsname: Optional[str]
    scopes: Optional[List[str]]

    class Config:
        anystr_strip_whitespace = True


class AccessTokenAuthorization(BaseModel):
    """AccessToken-Authorization."""

    permissions: Optional[List[Permission]]


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

    roles: Optional[List[str]]
    verify_caller: Optional[bool]

    class Config:
        anystr_strip_whitespace = True


class AccessToken(BaseModel):
    """AccessToken."""

    acr: Optional[str]
    address: Optional[AddressClaimSet]
    allowed_origins: Optional[List[str]] = Field(None, alias="allowed-origins")
    at_hash: Optional[str]
    auth_time: Optional[int]
    authorization: Optional[AccessTokenAuthorization]
    azp: Optional[str]
    birthdate: Optional[str]
    c_hash: Optional[str]
    category: Optional[AccessTokenCategory]
    claims_locales: Optional[str]
    cnf: Optional[str] = Field(None, alias="x5t#S256")
    email: Optional[str]
    email_verified: Optional[bool]
    exp: Optional[int]
    family_name: Optional[str]
    gender: Optional[str]
    given_name: Optional[str]
    iat: Optional[int]
    iss: Optional[str]
    jti: Optional[str]
    locale: Optional[str]
    middle_name: Optional[str]
    name: Optional[str]
    nbf: Optional[int]
    nickname: Optional[str]
    nonce: Optional[str]
    other_claims: Optional[Dict[str, Any]] = Field(None, alias="otherClaims")
    phone_number: Optional[str]
    phone_number_verified: Optional[bool]
    picture: Optional[str]
    preferred_username: Optional[str]
    profile: Optional[str]
    realm_access: Optional[AccessTokenAccess]
    s_hash: Optional[str]
    scope: Optional[str]
    session_state: Optional[str]
    sid: Optional[str]
    sub: Optional[str]
    tenants: Optional[List[str]]
    trusted_certs: Optional[List[str]] = Field(None, alias="trusted-certs")
    typ: Optional[str]
    updated_at: Optional[int]
    website: Optional[str]
    zoneinfo: Optional[str]

    class Config:
        anystr_strip_whitespace = True
        allow_population_by_field_name = True


class TokenResponse(BaseModel):
    """Represent Keycloak token response."""

    access_token: str
    expires_in: Optional[int]
    refresh_expires_in: Optional[int]
    refresh_token: Optional[str]
    token_type: str
    id_token: Optional[str]
    not_before_policy: Optional[int] = Field(None, alias="not-before-policy")
    session_state: Optional[str]
    scope: Optional[str]

    class Config:
        anystr_strip_whitespace = True
        allow_population_by_field_name = True


class OAuthRequest(BaseModel):
    """Base class for authorization requests"""

    client_id: Optional[str]
    grant_type: str
    client_secret: Optional[str]


class TokenRequest(OAuthRequest):
    """Represent Keycloak token request."""

    username: str
    password: str
    grant_type: str = "password"
    scope: Optional[str] = None

    class Config:
        anystr_strip_whitespace = True

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


class ClientViewsUsersAccessToken(object):
    @classmethod
    async def create_instance(cls):
        instance = ClientViewsUsersAccessToken()
        instance.token = ""
        await instance.request_new_token()
        return instance

    async def request_new_token(self):
        auth_data = OAuthRequest(
            grant_type="client_credentials",
            client_id=conf.KEYCLOAK_ROLE_ClientViewsAllUsers_ID,
            client_secret=conf.KEYCLOAK_ROLE_ClientViewsAllUsers_SECRET,
        )
        realm = conf.KEYCLOAK_REALM
        token_data = await kc_query.get_token_v2(realm, auth_data)
        self.token = token_data.access_token
