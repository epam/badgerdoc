from dataclasses import dataclass
from typing import Optional


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
]


async def get_menu(roles: list[str], tenant: str) -> list[MenuItem]:
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

    return menu
