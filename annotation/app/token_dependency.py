"""
Dependency, that will validate X-Current-Tenant
and Authorization token
"""
from tenant_dependency import get_tenant_info

TOKEN = get_tenant_info(url="http://bagerdoc-keycloack", algorithm="RS256")
