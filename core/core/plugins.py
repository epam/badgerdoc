import logging
import os
from typing import Optional

from sqlalchemy import Column, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


class PluginNotFoundError(Exception):
    pass


class Plugin(Base):
    """Database model for storing plugin information."""

    __tablename__ = "core_plugins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant: Mapped[str] = mapped_column(String(32))

    name: Mapped[str] = mapped_column(String(32))
    version: Mapped[str] = mapped_column(String(16))

    menu_name: Mapped[str] = mapped_column(String(16))

    description: Mapped[str] = mapped_column(String(10_000))
    url: Mapped[str] = mapped_column(String(256))
    is_iframe: Mapped[bool] = mapped_column(default=False)
    is_autoinstalled: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return (
            f"<Plugin(id={self.id}, tenant='{self.tenant}', name='{self.name}', "
            f"version='{self.version}', menu_name='{self.menu_name}')>"
        )


async def register_plugin(
    db_session: AsyncSession,
    name: str,
    version: str,
    menu_name: str,
    description: str,
    url: str,
    is_iframe: bool = False,
    is_autoinstalled: bool = False,
    tenant: Optional[str] = None,
) -> None:
    """
    Register a new plugin in the database.

    Args:
        db_session: SQLAlchemy AsyncSession for database operations
        name: Unique identifier for the plugin
        menu_name: Display name for the plugin in the menu
        description: Brief description of the plugin functionality
        version: Plugin version string
        url: URL endpoint for the plugin
        tenant: Tenant identifier for multi-tenant support

    Returns:
        None
    """
    logger.debug("Registering plugin '%s' for tenant: %s", name, tenant)
    if tenant is None:
        tenant = "*"
    new_plugin = Plugin(
        tenant=tenant,
        name=name,
        menu_name=menu_name,
        description=description,
        version=version,
        url=url,
        is_iframe=is_iframe,
        is_autoinstalled=is_autoinstalled,
    )
    db_session.add(new_plugin)
    await db_session.commit()
    logger.info("Created new plugin '%s' for tenant: %s", name, tenant)


async def get_plugins(db_session: AsyncSession, tenant: str) -> list[Plugin]:
    """
    Retrieve all plugins registered for a specific tenant.

    Args:
        db_session: SQLAlchemy AsyncSession for database operations
        tenant: Tenant identifier to filter plugins

    Returns:
        List of Plugin objects for the specified tenant
    """
    result = await db_session.execute(
        Plugin.__table__.select().where(Plugin.tenant == tenant)
    )
    plugins = result.all()
    logger.debug("Retrieved %d plugins for tenant: %s", len(plugins), tenant)
    return plugins


async def update_plugin(
    db_session: AsyncSession,
    plugin_id: int,
    menu_name: str,
    description: str | None,
    url: str,
    is_iframe: bool,
    is_autoinstalled: bool = False,
    tenant: str | None = None,
) -> None:
    """
    Update an existing plugin in the database.

    Args:
        db_session: SQLAlchemy AsyncSession for database operations
        plugin_id: ID of the plugin to update
        menu_name: Updated display name for the plugin in the menu
        description: Updated description of the plugin functionality
        url: Updated URL endpoint for the plugin
        is_iframe: Whether the plugin should be displayed in an iframe
        is_autoinstalled: Whether the plugin is automatically installed
        tenant: Tenant identifier for multi-tenant support

    Returns:
        Updated Plugin object or None if plugin not found
    """
    logger.debug("Updating plugin %d for tenant: %s", plugin_id, tenant)

    # Construct query to find the plugin by ID and tenant
    query = select(Plugin).where(Plugin.id == plugin_id)
    if tenant is not None:
        query = query.where(Plugin.tenant == tenant)

    # Execute the query
    result = await db_session.execute(query)
    plugin = result.scalar_one_or_none()

    if not plugin:
        logger.warning("Plugin %d not found for tenant: %s", plugin_id, tenant)
        raise PluginNotFoundError(
            f"Plugin with ID {plugin_id} not found for tenant: {tenant}"
        )

    # Update plugin attributes
    plugin.menu_name = menu_name
    plugin.description = description
    plugin.url = url
    plugin.is_iframe = is_iframe
    plugin.is_autoinstalled = is_autoinstalled

    await db_session.commit()
