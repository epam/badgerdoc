## How to use

Import and create an instance of tenant dependency.
All you need to make dependency work is a signature key.

```Python
from tenants import TenantData, get_tenant_info


SECRET = "some_secret_key"

tenant = get_tenant_info(SECRET, debug=True)
```
Param `debug` is needed to render `Authorize` button in `/openapi` docs.

Now you can add this dependency to your FastAPI endpoint:

```Python
from fastapi import Depends, FastAPI
from tenants import TenantData, get_tenant_info

SECRET = "some_secret_key"


app = FastAPI()
tenant = get_tenant_info(SECRET, debug=True)


@app.post("/test")
async def get_nums(token: TenantData = Depends(tenant)):
    return token.dict()
```

Go to docs and check how it works.

![alt text](https://fv9-2.failiem.lv/thumb_show.php?i=hx4e8gzj8&view)

1) Click `Authorize` and submit token.
2) Try to use endpoint.

Without valid jwt this endpoint `/test` will raise 401 Error.


```Python
@app.post("/test")
async def get_nums(token: TenantData = Depends(tenant)):
    return token.dict()
```
This dependency will:
1) Check if incoming request came with header `Authorization`, if that header wasn't provided Error 401 will be raised.
2) If header `Authorization` exists, dependency will try to validate it with signature key that you put as a first arg to dependency here -> `tenant = get_tenant_info(SECRET, debug=True)`. If key invalid or token expired 401 Error will be raised.
3) If token is valid dependency will parse token's body and get data from it. Token must contain data about `tenant`, `user_id` and `roles`, otherwise 403 error will be raised.
4) If previous steps were successful, your endpoint can do anything further, and you can work with `token` arg that is actually is a pydantic model, so you can work with it like you work with other pydantic models.
