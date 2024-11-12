## How to use with BadgerDoc

Import and create an instance of tenant dependency.
To make this dependency work with BadgerDoc you need to provide an url to keycloak and set 'algorithm' arg to `RS256`.

```Python
from tenant_dependency import TenantData, get_tenant_info

#  inner url would look like this "http://badgerdoc-keycloak" (http://{keycloak_pod_name})
#  outer url would look like this "http://dev1.gcov.ru"

tenant = get_tenant_info(url="http://dev1.gcov.ru", algorithm="RS256", debug=True)
```
## Note:
#### If you're using algorithm RS256 (Current BadgerDoc algorithm) you don't need arg "key", use only "url".
#### Otherwise, if you're using algorithm HS256, you need "key" arg and don't need "url". Check `usage_example/main.py`.
Param `debug` is needed to render `Authorize` button in `/openapi` docs.

Now you can add this dependency to your FastAPI endpoint:

```Python
from fastapi import Depends, FastAPI
from tenant_dependency import TenantData, get_tenant_info

app = FastAPI()
tenant = get_tenant_info(url="http://dev1.gcov.ru", algorithm="RS256", debug=True)


@app.post("/test")
async def get_nums(token: TenantData = Depends(tenant)):
    return token.dict()
```
Default values for `algorithm` and `debug` is `RS256` and `True`,
so you can create an instance like that:
```Python
tenant = get_tenant_info(url="http://dev1.gcov.ru")
```


Go to docs and check how it works.

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
2) If header `Authorization` exists, dependency will try to validate it with signature key or url those you put as args to dependency `tenant = get_tenant_info(key="SECRET") / tenant = get_tenant_info(url="http://bagerdoc-keycloack")`. If is key invalid or token is expired 401 Error will be raised.
3) It also checks header for arg "X-Current-Tenant", so if that arg isn't provided 401 will be raised. In case "X-Current-Tenant" provided dependency will check "X-Current-Tenant" containing in `tenants` array. Raises 401 if check wasn't successful.
4) If token is valid dependency will parse token's body and get data from it. Token must contain data about `tenants`, `user_id` and `roles`, otherwise 403 error will be raised.
5) If previous steps were successful, your endpoint can do anything further, and you can work with `token` arg that is actually is a pydantic model, so you can work with it like you work with other pydantic models.
