import logging
import os

from fastapi import APIRouter, Depends, Header
from tenant_dependency import TenantData, get_tenant_info

from core.services import menu
from core.utils import db

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST")
KEYCLOAK_SYSTEM_USER_SECRET = os.getenv("KEYCLOAK_SYSTEM_USER_SECRET", "")

tenant = get_tenant_info(
    KEYCLOAK_SYSTEM_USER_SECRET,
    algorithm="RS256",
    url=KEYCLOAK_HOST,
    debug=True,
)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

router = APIRouter(
    prefix="/menu",
    tags=["menu"],
)


@router.get("")
async def get_menu(
    token_data: TenantData = Depends(tenant),
    current_tenant: str | None = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(db.get_session),
) -> list[menu.MenuItem]:
    """
    Get the menu for the current tenant.
    """
    logger.debug("Fetching menu for roles: %s", token_data.roles)
    return await menu.get_menu(db_session, token_data.roles, current_tenant)
