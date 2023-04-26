from fastapi import FastAPI  # type: ignore

from convert.config import API_NAME, API_VERSION, settings
from convert.logger import get_logger
from convert.routers import coco, labelstudio, pdf, text

LOGGER = get_logger(__file__)

app = FastAPI(
    title=API_NAME,
    description="This service implements converting",
    version=API_VERSION,
    root_path=settings.root_path,
    servers=[{"url": settings.root_path}],
)
app.include_router(coco.router)
app.include_router(labelstudio.router)
app.include_router(text.router)
app.include_router(pdf.router)
