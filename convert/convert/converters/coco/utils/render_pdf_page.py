from pathlib import Path
from typing import List, Optional
from zipfile import ZipFile

import pdfplumber

from convert.config import settings
from convert.converters.coco.utils.common_utils import (
    add_to_zip_and_local_remove,
)
from convert.logger import get_logger

LOGGER = get_logger(__file__)


def pdf_page_to_jpg(
    file: Path,
    output_path: Path,
    zip_file: ZipFile,
    job_id: int,
    validated_pages: Optional[List[int]] = None,
) -> None:
    """Render page validated image from pdf document"""
    with pdfplumber.open(file) as pdf:
        LOGGER.info(
            "Start pages rendering for job %s, file %s",
            job_id,
            Path(file).name,
        )
        for num, page in enumerate(pdf.pages, 1):
            if validated_pages and num not in validated_pages:
                continue
            image = page.to_image(resolution=settings.dpi).original
            image_path = (
                output_path / f"{job_id}_{num}.{settings.coco_image_format}"
            )
            image.save(image_path)
            LOGGER.info(
                "Page %s was rendered and saved to %s", num, image_path
            )
            LOGGER.info(
                "Page %s was written to archive %s", num, zip_file.filename
            )
            LOGGER.info("Page %s was removed", num)
            add_to_zip_and_local_remove(str(image_path), zip_file)
