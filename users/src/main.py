from typing import Any, Callable, Dict, List, Optional

import aiohttp
import pydantic
import src.config as conf
import src.keycloak.query as kc_query
import src.keycloak.schemas as kc_schemas
import src.keycloak.utils as kc_utils
from aiohttp.web_exceptions import HTTPException as AIOHTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from email_validator import EmailNotValidError, validate_email
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from src import s3, utils
from src.config import (
    KEYCLOAK_ROLE_ADMIN,
    KEYCLOAK_USERS_PUBLIC_KEY,
    ROOT_PATH,
)
from src.schemas import Users
from tenant_dependency import TenantData, get_tenant_info
from urllib3.exceptions import MaxRetryError

app = FastAPI(title="users", root_path=ROOT_PATH, version="0.1.2")
realm = conf.KEYCLOAK_REALM
minio_client = s3.get_minio_client()

tenant = get_tenant_info(
    KEYCLOAK_USERS_PUBLIC_KEY, algorithm="RS256", debug=True
)


def check_authorization(token: TenantData, role: str) -> None:
    if role not in token.roles:
        raise HTTPException(status_code=403, detail="Access denied")


@app.middleware("http")
async def request_error_handler(
    request: Request, call_next: Callable[..., Any]
) -> Any:
    try:
        return await call_next(request)
    except aiohttp.ClientResponseError as err:
        return JSONResponse(
            status_code=err.status, content={"detail": err.message}
        )
    except AIOHTTPException as err:
        return JSONResponse(
            status_code=err.status_code, content={"detail": err.reason}
        )


@app.post(
    "/token",
    status_code=200,
    response_model=kc_schemas.TokenResponse,
    tags=["auth"],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> kc_schemas.TokenResponse:
    """Get auth token."""
    try:
        credentials = kc_schemas.TokenRequest.from_fastapi_form(form_data)
    except pydantic.ValidationError as err:
        raise HTTPException(status_code=422, detail=err.errors())
    return await kc_query.get_token_v2(realm, credentials)


@app.post(
    "/refresh_token",
    status_code=200,
    response_model=kc_schemas.TokenResponse,
)
async def refresh_token(
    request_data: kc_schemas.RefreshTokenRequest,
) -> kc_schemas.TokenResponse:
    """Refresh token."""
    return await kc_query.get_token_v2(realm, request_data)


@app.post("/users/registration", status_code=201, tags=["users"])
async def user_registration(
    email: str,
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> Dict[str, str]:
    """Register new user"""
    check_authorization(token, KEYCLOAK_ROLE_ADMIN)

    try:
        validate_email(email)
    except EmailNotValidError as error:
        raise HTTPException(status_code=400, detail=str(error))

    await kc_query.create_user(
        token=token.token, realm=realm, username=email, email=email
    )
    user = await kc_query.get_users_v2(
        realm=realm, token=token.token, email=email, exact="true"
    )
    user_id = user[0].id
    await kc_query.execute_action_email(
        token=token.token, realm=realm, user_id=user_id
    )
    return {"detail": "User has been created"}


@app.get(
    "/users/current",
    status_code=200,
    response_model=kc_schemas.User,
    tags=["users"],
    deprecated=True,
)
async def get_user_data_from_jwt(
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> kc_schemas.User:
    """Get user from realm with JWT"""
    return await kc_query.get_user(realm, token.token, token.user_id)


@app.get("/users/current_v2", status_code=200, tags=["users"])
async def get_user_info_from_token_introspection(
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> kc_query.Token_Data:
    """Get user_info from realm through JWT introspection"""
    return await kc_query.introspect_token(token.token)


@app.get(
    "/users/{user_id}",
    status_code=200,
    response_model=kc_schemas.User,
    tags=["users"],
)
async def get_user(
    user_id: str,
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> kc_schemas.User:
    """Get user from realm."""
    return await kc_query.get_user(realm, token.token, user_id)


@app.get(
    "/tenants", status_code=200, response_model=List[str], tags=["tenants"]
)
async def get_tenants(
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> List[str]:
    """Get all tenants."""
    return [
        group.name for group in await kc_query.get_groups(realm, token.token)
    ]


@app.post(
    "/tenants",
    status_code=201,
    response_model=Dict[str, str],
    tags=["tenants"],
)
async def create_tenant(
    tenant: str = Query(..., regex="^[a-z0-9][a-z0-9\\.\\-]{1,61}[a-z0-9]$"),
    token: TenantData = Depends(tenant),
    bucket: str = Depends(utils.get_bucket_name),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> Dict[str, str]:
    """Create new tenant."""
    check_authorization(token, KEYCLOAK_ROLE_ADMIN)
    try:
        s3.create_bucket(minio_client, bucket)
    except MaxRetryError:
        raise HTTPException(
            status_code=503, detail="Cannot connect to the Minio."
        )
    tenant_ = kc_schemas.Group(name=tenant)
    await kc_query.create_group(realm, token.token, tenant_)
    return {"detail": "Tenant has been created"}


@app.put(
    "/tenants/{tenant}/users/{user_id}",
    status_code=200,
    response_model=Dict[str, str],
    tags=["tenants"],
)
async def add_user_to_tenant(
    user_id: str,
    tenant: str,
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> Dict[str, str]:
    """Add user to tenant."""
    check_authorization(token, KEYCLOAK_ROLE_ADMIN)
    tenant_ = await kc_query.get_groups(realm, token.token, tenant)
    if not tenant_ or all([t.name != tenant for t in tenant_]):
        raise HTTPException(status_code=404, detail="Tenant not found")
    user = await kc_query.get_user(realm, token.token, user_id)
    user.add_tenant(tenant)
    await kc_query.update_user(realm, token.token, user_id, user)
    return {"detail": "User has been added to the tenant"}


@app.delete(
    "/tenants/{tenant}/users/{user_id}",
    status_code=200,
    response_model=Dict[str, str],
    tags=["tenants"],
)
async def remove_user_from_tenant(
    user_id: str,
    tenant: str,
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> Dict[str, str]:
    """Remove user from tenant."""
    check_authorization(token, KEYCLOAK_ROLE_ADMIN)
    user = await kc_query.get_user(realm, token.token, user_id)
    user.remove_tenant(tenant)
    await kc_query.update_user(realm, token.token, user_id, user)
    return {"detail": "User has been removed from the tenant"}


@app.post("/users/search", tags=["users"])
async def get_users_by_filter(
    users: Users,
    token: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> List[kc_schemas.User]:
    """Getting a list of users from keycloak by substring"""

    filters = kc_utils.create_filters(users)

    if filters.get("role") is not None:
        users_list = await kc_query.get_users_by_role(
            token=token.token,
            realm=realm,
            role=filters.get("role").value,  # type: ignore
        )
    else:
        users_list = await kc_query.get_users_v2(
            realm=realm, token=token.token
        )

    users_list = kc_schemas.User.filter_users(
        users=users_list,
        user_name_substring=filters.get("name"),
        user_id=filters.get("id"),  # type: ignore
    )

    return users_list


@app.get("/identity_providers_data", tags=["general info"])
async def get_idp_names_and_SSOauth_links() -> Dict[str, List[Dict[str, str]]]:
    """Provides names and links to authenticate with
    for all Identity Providers set in Keycloak"""

    auth_response = await kc_query.get_master_realm_auth_data()
    master_realm_access_token = auth_response["access_token"]

    identity_providers_data = await kc_query.get_identity_providers_data(
        master_realm_access_token
    )
    identity_providers_data_needed = utils.extract_idp_data_needed(
        identity_providers_data
    )

    return {"Identity Providers Info": identity_providers_data_needed}


@app.on_event("startup")
def periodic() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        utils.delete_file_after_7_days,
        kwargs={"client": minio_client},
        trigger="cron",
        hour="*/1",
    )
    scheduler.start()
