import json
import logging
from pathlib import Path
from typing import Any, List, Tuple

from .common import models as m
from .common.minio_utils import MinioCommunicator

logger = logging.getLogger(__name__)


def get_document(
    loader: MinioCommunicator, work_dir: Path, request: m.ClassifierRequest
) -> Path:
    """Get a document from s3-storage."""
    logger.info("Get a document from minio")
    document_path = work_dir / request.file.name
    loader.client.fget_object(
        request.bucket, str(request.file), str(document_path)
    )
    return document_path


def get_annotation(
    loader: MinioCommunicator, work_dir: Path, request: m.ClassifierRequest
) -> List[m.PageDOD]:
    """Get an annotation from s3-storage."""
    logger.info("Get an annotation from minio")
    annotation_input_path = work_dir / request.input_path
    loader.client.fget_object(
        request.bucket, str(request.input_path), str(annotation_input_path)
    )
    annotation = m.AnnotationFromS3.parse_obj(
        json.loads(annotation_input_path.read_text())
    )
    return annotation.pages


def put_annotation(
    loader: MinioCommunicator,
    work_dir: Path,
    annotation: List[m.PageDOD],
    request: m.ClassifierRequest,
) -> None:
    """Put an annotation to s3-storage."""
    logger.info("Put an annotation to minio")
    updated_annotation_path = Path(work_dir) / f"out_{request.input_path.name}"
    output_annotation = m.AnnotationFromS3(pages=annotation).json(
        by_alias=True
    )
    updated_annotation_path.write_text(output_annotation)
    loader.client.fput_object(
        request.output_bucket,
        str(request.output_path),
        str(updated_annotation_path),
    )


# todo: use abc for loader
def download_model(
    bucket: str, model_files: Tuple[str, ...], destination: Path, loader: Any
) -> Path:
    """Get an ML model and a config file from s3-storage."""
    logger.info("Get an ML model and a config file from minio")
    destination.mkdir(parents=True, exist_ok=True)
    if all((destination / fi).exists() for fi in model_files):
        return destination
    # todo: add checking of downloading
    for fi in model_files:
        loader.client.fget_object(bucket, fi, str(destination / Path(fi).name))
    logger.info(list(destination.iterdir()))
    return destination
