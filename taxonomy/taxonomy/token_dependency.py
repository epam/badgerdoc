"""
Dependency, that will validate X-Current-Tenant
and Authorization token
"""
import os

from tenant_dependency import TenantData, get_tenant_info

KEYCLOAK_HOST = os.getenv('KEYCLOAK_HOST')
TOKEN = get_tenant_info(url=KEYCLOAK_HOST, algorithm="RS256")

if os.getenv("TAXONOMY_NO_AUTH", False):
    TOKEN = lambda: TenantData(  # noqa: E731
        token="TEST_TOKEN",
        user_id="UUID",
        roles=["role"],
        tenants=["TEST_TENANT"],
    )
