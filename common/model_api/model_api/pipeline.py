"""Inference of a pdf document
    and exchange with s3-storage.
"""
import logging
from pathlib import Path
from typing import Any

import pdfplumber

from .common import models as m
from .common.minio_utils import MinioCommunicator
from .storage_exchange import get_annotation, get_document, put_annotation
from .utils import (form_response, get_needs_from_request_and_annotation,
                    update_annotation_categories)

logger = logging.getLogger(__name__)


def pipeline(
    get_model: Any,
    inference: Any,
    request: m.ClassifierRequest,
    loader: MinioCommunicator,
    work_dir: Path,
) -> m.ClassifierResponse:
    """Download data from s3-storage, run inference and save to s3-storage."""
    logger.info("Start processing")

    document_path = get_document(loader, work_dir, request)
    annotation = get_annotation(loader, work_dir, request)
    model = get_model()

    (
        needed_pages,
        obj_ids_in_the_request,
    ) = get_needs_from_request_and_annotation(annotation, request.input_field)

    with pdfplumber.open(document_path) as pdf:
        for page in needed_pages:
            logger.info("Inference of a page %s", page.page_num)
            update_annotation_categories(
                inference,
                model,
                page,
                pdf,
                list(request.input_field.keys()),
                work_dir,
                tuple(obj_ids_in_the_request),
            )

    put_annotation(loader, work_dir, annotation, request)
    response = form_response(annotation, request.input_field)
    return m.ClassifierResponse(__root__=response)
