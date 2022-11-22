"""
Dependency, that will validate X-Current-Tenant
and Authorization token
"""
from tenant_dependency import TenantData

TOKEN = lambda: TenantData(
    token="TEST_TOKEN", user_id="UUID", roles=["role"], tenants=["TEST_TENANT"]
)

# from tenant_dependency import get_tenant_info

# TOKEN = get_tenant_info(url="http://bagerdoc-keycloack", algorithm="RS256")
