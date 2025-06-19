import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.routes import menus, plugins

ROOT_PATH = os.getenv("ROOT_PATH", "")
KEYCLOAK_SYSTEM_USER_SECRET = os.getenv("KEYCLOAK_SYSTEM_USER_SECRET", "")

with open("version.txt", "r") as f:
    __version__ = f.read().strip()

app = FastAPI(title="core", root_path=ROOT_PATH, version=__version__)
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST")

if WEB_CORS := os.getenv("WEB_CORS", ""):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=WEB_CORS.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(menus.router)
app.include_router(plugins.router)
