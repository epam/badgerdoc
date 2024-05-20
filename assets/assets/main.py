import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tenant_dependency import get_tenant_info

from assets import routers
from assets.config import settings

tenant = get_tenant_info(url=settings.keycloak_host, algorithm="RS256")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    root_path=settings.root_path,
    servers=[{"url": settings.root_path}],
    dependencies=[Depends(tenant)],
)

if WEB_CORS := os.getenv("WEB_CORS", ""):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=WEB_CORS.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(routers.minio_router.router)
app.include_router(routers.files_router.router)
app.include_router(routers.datasets_router.router)
app.include_router(routers.bonds_router.router)
app.include_router(routers.s3_router.router)
