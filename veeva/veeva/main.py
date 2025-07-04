import logging
import os

from fastapi import FastAPI

from veeva.routes import configurations, synchronization

ROOT_PATH = os.getenv("ROOT_PATH", "/veeva")

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG").upper())

app = FastAPI(
    title="BadgerDoc Veeva PM Synchronization Service",
    description="A microservice that synchronizes Veeva Promomats with BadgerDoc",
    version=open("version.txt").read().strip(),
    root_path=ROOT_PATH,
)

app.include_router(configurations.router)
app.include_router(synchronization.router)
