from fastapi import FastAPI  # type: ignore

from src.config import API_NAME, API_VERSION, settings
from src.logger import get_logger
<<<<<<< HEAD
from src.routers import coco, label_studio, pdf, text
=======
from src.routers import coco, labelstudio, text
>>>>>>> b7a4b44 (test: Add tests)

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
