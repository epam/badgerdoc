import logging
import os
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tenant_dependency import TenantData, get_tenant_info

import core.menu
import core.plugins
from core.db import get_session

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


@app.get("/menu", tags=["general"])
async def get_menu(
    token_data: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(get_session),
):
    """
    Get the menu for the current tenant.
    """
    logger.debug("Fetching menu for roles: %s", token_data.roles)
    return await core.menu.get_menu(db_session, token_data.roles, current_tenant)


class Plugin(BaseModel):
    name: str
    menu_name: str
    description: str
    version: str
    url: str
    is_iframe: bool


@app.post("/plugins", tags=["plugins"])
async def register_plugin(
    plugin: Plugin,
    token_data: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(get_session),
):
    """
    Create a new plugin for the current tenant.
    """
    if "admin" not in token_data.roles:
        logger.error("Unauthorized access attempt user: %s", token_data)
        return {"error": "Unauthorized"}, 403
    # Placeholder for plugin creation logic
    logger.debug("Creating plugin for tenant: %s", current_tenant)
    await core.plugins.register_plugin(
        db_session,
        name=plugin.name,
        menu_name=plugin.menu_name,
        description=plugin.description,
        version=plugin.version,
        url=plugin.url,
        is_iframe=plugin.is_iframe,
        tenant=current_tenant,
    )
    return {"message": "Plugin created successfully", "tenant": current_tenant}


class PluginResponse(BaseModel):
    id: int
    name: str
    menu_name: str
    description: Optional[str]
    version: str
    url: str
    tenant: Optional[str]


@app.get("/plugins", tags=["plugins"])
async def list_plugins(
    token_data: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(get_session),
):
    """
    List all plugins for the current tenant.
    """
    if "admin" not in token_data.roles:
        logger.error("Unauthorized access attempt user: %s", token_data)
        return {"error": "Unauthorized"}, 403

    logger.debug("Listing plugins for tenant: %s", current_tenant)
    db_plugins = await core.plugins.get_plugins(db_session, current_tenant)

    # Convert SQLAlchemy model objects to Pydantic models
    plugins = [
        PluginResponse(
            id=plugin.id,
            name=plugin.name,
            menu_name=plugin.menu_name,
            description=plugin.description,
            version=plugin.version,
            url=plugin.url,
            tenant=plugin.tenant,
        )
        for plugin in db_plugins
    ]

    return {
        "plugins": plugins,
        "tenant": current_tenant,
    }


class PluginUpdate(BaseModel):
    menu_name: str
    description: str | None = None
    url: str
    is_iframe: bool


class UpdatedPluginResponse(BaseModel):
    id: int


@app.put("/plugins/{plugin_id}", tags=["plugins"])
async def update_plugin(
    plugin_id: int,
    plugin: PluginUpdate,
    token_data: TenantData = Depends(tenant),
    current_tenant: str | None = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(get_session),
) -> UpdatedPluginResponse:
    """
    Update an existing plugin for the current tenant.

    Name and version cannot be updated as they form a unique constraint.
    Only menu_name, description, URL and display settings can be modified.
    """
    if "admin" not in token_data.roles:
        logger.error("Unauthorized access attempt user: %s", token_data)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to update plugins",
        )

    logger.debug("Updating plugin %s for tenant: %s", plugin_id, current_tenant)

    try:
        await core.plugins.update_plugin(
            db_session,
            plugin_id=plugin_id,
            menu_name=plugin.menu_name,
            description=plugin.description,
            url=plugin.url,
            is_iframe=plugin.is_iframe,
        )

        # if not updated_plugin:
        #    raise HTTPException(
        #        status_code=status.HTTP_404_NOT_FOUND,
        #        detail=f"Plugin with ID {plugin_id} not found for tenant {current_tenant}",
        #    )

        return UpdatedPluginResponse(
            id=plugin_id,
        )

    except Exception as e:
        logger.error("Error updating plugin: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating plugin: {str(e)}",
        )
