import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from tenant_dependency import TenantData

from core.routes import dependencies
from core.services import plugin
from core.utils import db

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/plugins",
    tags=["plugins"],
)


class PluginRequest(BaseModel):
    name: str
    menu_name: str
    description: str
    version: str
    url: str
    is_iframe: bool
    is_autoinstalled: bool


@router.post("", tags=["plugins"])
async def register_plugin(
    plugin_request: PluginRequest,
    _: TenantData = Depends(dependencies.require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(db.get_session),
) -> plugin.Plugin:
    """
    Create a new plugin for the current tenant.
    """
    # Placeholder for plugin creation logic
    logger.debug("Creating plugin for tenant: %s", current_tenant)
    try:
        new_plugin = await plugin.Plugin(
            name=plugin_request.name,
            menu_name=plugin_request.menu_name,
            description=plugin_request.description,
            version=plugin_request.version,
            url=plugin_request.url,
            is_iframe=plugin_request.is_iframe,
            tenant=current_tenant,
        ).register(
            db_session,
        )
    except plugin.PluginAlreadyExistsError as e:
        logger.error("Plugin already exists: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return new_plugin


@router.get("", tags=["plugins"])
async def list_plugins(
    _: TenantData = Depends(dependencies.require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(db.get_session),
) -> list[plugin.Plugin]:
    logger.debug("Listing plugins for tenant: %s", current_tenant)
    return await plugin.Plugin(tenant=current_tenant).get_plugins(db_session)


class PluginUpdateRequest(BaseModel):
    menu_name: str
    description: str | None = None
    url: str
    is_iframe: bool


@router.put("/plugins/{plugin_id}", tags=["plugins"])
async def update_plugin(
    plugin_id: int,
    plugin_request: PluginUpdateRequest,
    _: TenantData = Depends(dependencies.require_admin_role),
    current_tenant: str | None = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(db.get_session),
) -> plugin.Plugin:
    logger.debug(
        "Updating plugin %s for tenant: %s", plugin_id, current_tenant
    )

    try:
        return await plugin.Plugin(
            id=plugin_id,
            menu_name=plugin_request.menu_name,
            description=plugin_request.description,
            url=plugin_request.url,
            is_iframe=plugin_request.is_iframe,
            tenant=current_tenant,
        ).update(
            db_session,
        )

    except plugin.PluginNotFoundError as e:
        logger.error("Error updating plugin: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error updating plugin: {str(e)}",
        )


@router.delete("/plugins/{plugin_id}", tags=["plugins"])
async def delete_plugin(
    plugin_id: int,
    _: TenantData = Depends(dependencies.require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(db.get_session),
) -> plugin.Plugin:
    logger.debug(
        "Deleting plugin %s for tenant: %s", plugin_id, current_tenant
    )
    try:
        return await plugin.Plugin(
            id=plugin_id, tenant=current_tenant
        ).delete_plugin(db_session)
    except plugin.PluginNotFoundError:
        logger.error(
            "Plugin with ID %s not found for tenant %s",
            plugin_id,
            current_tenant,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin with ID {plugin_id} not found for tenant {current_tenant}",
        )
