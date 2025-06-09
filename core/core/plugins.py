import logging
import os
from typing import Optional

from sqlalchemy import Column, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


class Plugin(Base):
    """Database model for storing plugin information."""

    __tablename__ = "core_plugins"

    name = Column(String(255), primary_key=True)
    menu_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    url = Column(String(255), nullable=False)
    tenant = Column(String(255), primary_key=True, nullable=True)

    def __repr__(self):
        return f"<Plugin(name='{self.name}', tenant='{self.tenant}')>"


async def register_plugin(
    db_session: AsyncSession,
    name: str,
    menu_name: str,
    description: str,
    version: str,
    url: str,
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
    new_plugin = Plugin(
        name=name,
        menu_name=menu_name,
        description=description,
        version=version,
        url=url,
        tenant=tenant,
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
