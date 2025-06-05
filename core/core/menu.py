import os
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.plugins import get_plugins

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST")


@dataclass
class MenuItem:
    name: str
    url: str
    is_external: bool = False
    is_iframe: bool = False
    iframe_url: str = ""
    children: Optional[list["MenuItem"]] = None


AUTHORIZED_USER_COMMON_MENU = [
    MenuItem(
        name="Documents",
        url="/documents",
    ),
    MenuItem(
        name="My Tasks",
        url="/my tasks",
    ),
]


ADMIN_USER_MENU = [
    MenuItem(
        name="Jobs",
        url="/jobs",
    ),
    MenuItem(
        name="Categories",
        url="/categories",
    ),
    MenuItem(
        name="Reports",
        url="/reports",
    ),
    MenuItem(
        name="Settings",
        url="/settings",
        children=[
            MenuItem(
                name="Plugins",
                url="/plugins",
            ),
            MenuItem(
                name="Keycloak",
                url=KEYCLOAK_HOST,
                is_external=True,
            ),
        ],
    ),
]


async def get_menu(
    db_session: AsyncSession, roles: list[str], tenant: str
) -> list[MenuItem]:
    """
    Get the menu items based on user roles.

    Args:
        roles: List of user roles.

    Returns:
        List of MenuItem objects.
    """
    menu = []

    menu.extend(AUTHORIZED_USER_COMMON_MENU)
    if "admin" in roles:
        menu.extend(ADMIN_USER_MENU)

    plugins = await get_plugins(db_session, tenant)
    if plugins:
        menu.append(
            MenuItem(
                name="Plugins",
                url="/plugins",
                is_iframe=False,
                children=[
                    MenuItem(
                        name=plugin.menu_name,
                        url=plugin.menu_name,
                        is_iframe=True,
                        iframe_url=plugin.url,
                    )
                    for plugin in plugins
                ],
            )
        )
    return menu
