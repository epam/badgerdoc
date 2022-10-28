from typing import Any

from fastapi import Depends, FastAPI

from tenants import TenantData, get_tenant_info

SECRET = "some_secret_key"


app = FastAPI()
tenant = get_tenant_info(SECRET, debug=True)
# tenant = get_tenant_info(SECRET, debug=True, scheme_name="Tenant JWT", description="some description here")


@app.post("/test")
async def get_nums(token: TenantData = Depends(tenant)) -> Any:
    return token.dict()
