import logging
import os
from typing import Optional

from fastapi import Depends, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from tenant_dependency import TenantData, get_tenant_info

import core.menu

ROOT_PATH = os.getenv("ROOT_PATH", "")
KEYCLOAK_SYSTEM_USER_SECRET = os.getenv("KEYCLOAK_SYSTEM_USER_SECRET", "")

with open("version.txt", "r") as f:
    __version__ = f.read().strip()

app = FastAPI(title="core", root_path=ROOT_PATH, version=__version__)
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST")

if WEB_CORS := os.getenv("WEB_CORS", ""):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=WEB_CORS.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )


tenant = get_tenant_info(
    KEYCLOAK_SYSTEM_USER_SECRET,
    algorithm="RS256",
    url=KEYCLOAK_HOST,
    debug=True,
)


@app.get("/menu")
async def get_menu(
    token_data: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
):
    """
    Get the menu for the current tenant.
    """
    logger.debug("Fetching menu for roles: %s", token_data.roles)
    return await core.menu.get_menu(token_data.roles, current_tenant)
