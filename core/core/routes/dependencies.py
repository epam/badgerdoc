import os

from fastapi import Depends, HTTPException, status
from tenant_dependency import TenantData, get_tenant_info

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST")
TENANT = get_tenant_info(url=KEYCLOAK_HOST, algorithm="RS256")


def require_admin_role(token_data: TenantData = Depends(TENANT)):
    """
    Dependency that checks if the user has admin role.
    Raises HTTPException if the user doesn't have admin privileges.
    """
    if "admin" not in token_data.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation",
        )
    return token_data
