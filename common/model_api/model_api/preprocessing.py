"""Crop bboxes from images"""
from decimal import Decimal
from pathlib import Path
from typing import Iterator, List, Tuple

from pdfplumber.page import Page
from PIL.Image import Image

from .common.models import PageDOD, Size
from .config import settings
from .logger import get_logger

logger = get_logger(__name__)
# if DPI is too small then Wand raise wand.exceptions.DelegateError
MINIMUM_WAND_DPI = 4


def crop_page_images(
    pdf_page: Page,
    dod_page: PageDOD,
    categories: List[str],
    output_path: Path,
) -> Iterator[Path]:
    for obj in dod_page.objs:
        if obj.category not in categories:
            continue

        figure_bbox = convert_figure_bbox_in_points(
            pdf_page.bbox, dod_page.size, obj.bbox
        )
        figure_image: Image = pdf_page.to_image(
            resolution=calculate_dpi(figure_bbox)
        ).original.crop(figure_bbox)
        image_path = (
            output_path / f"{obj.idx}.{settings.training_image_format}"
        )
        figure_image.save(str(image_path))
        yield image_path


def convert_figure_bbox_in_points(
    page_pdf_bbox: Tuple[Decimal, ...],
    page_dod_size: Size,
    figure_bbox: Tuple[float, float, float, float],
) -> Tuple[Decimal, ...]:
    page_width_inch = page_pdf_bbox[3] - page_pdf_bbox[1]
    page_height_inch = page_pdf_bbox[2] - page_pdf_bbox[0]
    try:
        figure_to_page_w_points = page_width_inch / Decimal(
            page_dod_size.width
        )
        figure_to_page_h_points = page_height_inch / Decimal(
            page_dod_size.height
        )
    except ZeroDivisionError as err:
        logger.error("Page size from DOD is wrong! %s", page_dod_size)
        raise err

    return tuple(
        (
            Decimal(figure_bbox[0]) * figure_to_page_w_points,
            Decimal(figure_bbox[1]) * figure_to_page_h_points,
            Decimal(figure_bbox[2]) * figure_to_page_w_points,
            Decimal(figure_bbox[3]) * figure_to_page_h_points,
        )
    )


def calculate_dpi(image_bbox: Tuple[Decimal, ...]) -> int:
    width = image_bbox[3] - image_bbox[1]
    height = image_bbox[2] - image_bbox[0]
    # 1 inch = 72 points
    resolution = round(settings.training_dpi / (min(width, height) / 72))
    return max(MINIMUM_WAND_DPI, resolution)
