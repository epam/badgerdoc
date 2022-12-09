from typing import Any

from fastapi import Depends, FastAPI, Header

from tenant_dependency import TenantData, get_tenant_info

# RS256 (BadgerDoc)
# url=http://dev1.gcov.ru for local testing, url=http://bagerdoc-keycloack for deployed service  # noqa
tenant_ = get_tenant_info(url="http://dev1.gcov.ru", algorithm="RS256")
app_ = FastAPI()


@app_.post("/test_")
async def some_(
    x_current_tenant: str = Header(...), token: TenantData = Depends(tenant_)
) -> Any:
    return {"token": token.dict(), "current tenant": x_current_tenant}


# HS256
SECRET = "some_secret_key"
tenant = get_tenant_info(key=SECRET, algorithm="HS256")
app = FastAPI()


@app.post("/test")
async def some(
    x_current_tenant: str = Header(...), token: TenantData = Depends(tenant)
) -> Any:
    return {"token": token.dict(), "current tenant": x_current_tenant}
