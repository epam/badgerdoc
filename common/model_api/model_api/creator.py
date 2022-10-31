import tempfile
from pathlib import Path
from typing import Any, Callable, Optional, Tuple, Union

from fastapi import FastAPI

from .common.minio_utils import MinioCommunicator
from .common.models import ClassifierRequest, ClassifierResponse
from .config import settings
from .logger import get_logger
from .pipeline import pipeline
from .storage_exchange import download_model

app = FastAPI()
logger = get_logger(__name__)


#  Todo: add a validation to the response.
# @app.post("/v1/models/name:predict", response_model=m.ClassifierResponse)
@app.post(f"{settings.request_prefix}/{settings.model_name}:predict")
def predict(request_data: ClassifierRequest) -> Union[ClassifierResponse, str]:
    """Run predict=inference of a document."""
    logger.info("Request: %s", request_data)
    for method in ("inference", "get_model"):
        if not hasattr(app, method):
            return f'Method "{method}" not implemented'
    with tempfile.TemporaryDirectory() as tmpdirname:
        response = pipeline(
            app.get_model,  # type: ignore
            app.inference,  # type: ignore
            request=request_data,
            loader=MinioCommunicator(),
            work_dir=Path(tmpdirname),
        )
    logger.info("Response: %s", response)
    return response


def create_app(
    get_model: Optional[Callable[[Any], Any]] = None,
    inference: Optional[Callable[[Any], Any]] = None,
    bucket: Optional[str] = None,
    model_files: Optional[Tuple[str, ...]] = None,
    destination: Optional[Path] = None,
    loader: Optional[Any] = None,
) -> FastAPI:
    if get_model:
        app.get_model = get_model  # type: ignore
    if inference:
        app.inference = inference  # type: ignore
    if all((bucket, model_files, destination, loader)):
        download_model(bucket, model_files, destination, loader)
    return app
