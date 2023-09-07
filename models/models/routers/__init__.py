from tenant_dependency import get_tenant_info

from models.constants import ALGORITHM, KEYCLOAK_HOST

tenant = get_tenant_info(url=KEYCLOAK_HOST, algorithm=ALGORITHM)
