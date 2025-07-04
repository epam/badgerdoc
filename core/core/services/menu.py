import os

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.services import plugin

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST")


class MenuItem(BaseModel):
    name: str
    badgerdoc_path: str
    is_external: bool = False
    is_iframe: bool = False
    url: str = ""
    children: list["MenuItem"] | None = None


AUTHORIZED_USER_COMMON_MENU = [
    MenuItem(
        name="Documents",
        badgerdoc_path="/documents",
    ),
    MenuItem(
        name="My Tasks",
        badgerdoc_path="/my tasks",
    ),
]


ADMIN_USER_MENU = [
    MenuItem(
        name="Jobs",
        badgerdoc_path="/jobs",
    ),
    MenuItem(
        name="Categories",
        badgerdoc_path="/categories",
    ),
    MenuItem(
        name="Reports",
        badgerdoc_path="/reports",
    ),
    MenuItem(
        name="Settings",
        badgerdoc_path="/settings",
        children=[
            MenuItem(
                name="Plugins",
                badgerdoc_path="/settings/plugins",
            ),
            MenuItem(
                name="Keycloak",
                badgerdoc_path="/settings/keycloak",
                is_external=True,
                url=KEYCLOAK_HOST,
            ),
        ],
    ),
]


def form_path(menu_name: str) -> str:
    """
    Form the path for the menu item based on its name.

    Args:
        menu_name: The name of the menu item.

    Returns:
        A formatted path string.
    """
    return f"/plugins/{menu_name.lower().replace(' ', '-')}"


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

    plugins = await plugin.Plugin(tenant=tenant).get_all(db_session)
    if plugins:
        menu.append(
            MenuItem(
                name="Plugins",
                badgerdoc_path="/plugins/",
                is_iframe=False,
                children=[
                    MenuItem(
                        name=f"{plugin.menu_name} ({plugin.version})",
                        badgerdoc_path=f"/plugins/{plugin.id}",
                        is_iframe=plugin.is_iframe,
                        url=plugin.url,
                    )
                    for plugin in plugins
                ],
            )
        )
    return menu
