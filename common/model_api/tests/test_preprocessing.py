from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

import model_api.preprocessing
from model_api.config import settings
from model_api.common.models import GeometryObject, PageDOD, Size
from model_api.preprocessing import (
    calculate_dpi,
    convert_figure_bbox_in_points,
    crop_page_images,
)

TEST_PDF = Path(__file__).parent / "test_files" / "test_pdf.pdf"


def test_calculate_figure_bbox_inch():
    result = convert_figure_bbox_in_points(
        page_pdf_bbox=(Decimal(0), Decimal(0), Decimal(1000), Decimal(500)),
        page_dod_size=Size(width=1000, height=2000),
        figure_bbox=(200, 100, 400, 300),
    )
    assert result == (Decimal(100), Decimal(50), Decimal(200), Decimal(150))


def test_calculate_bbox_zero_page_width():
    with pytest.raises(ZeroDivisionError):
        convert_figure_bbox_in_points(
            page_pdf_bbox=(Decimal(0), Decimal(0), Decimal(1), Decimal(1)),
            page_dod_size=Size(width=0, height=2000),
            figure_bbox=(200, 100, 400, 300),
        )


def test_calculate_dpi():
    dpi = calculate_dpi((Decimal(0), Decimal(0), Decimal(10), Decimal(10)))
    assert dpi == round(Decimal(settings.training_dpi) / Decimal(10) * 72)


def test_preprocessing(tmpdir, monkeypatch):
    obj1 = GeometryObject(category="1", bbox=(300, 300, 800, 800), id="object_id")
    obj2 = GeometryObject(category="100500", bbox=(0, 0, 0, 0), id="does not matter")
    page_dod = PageDOD(page_num=1, size=Size(width=595, height=841), objs=[obj1, obj2])

    page_mock = MagicMock()
    image_mock = MagicMock()
    page_mock.to_image = MagicMock(return_value=image_mock)
    convert = MagicMock(return_value=(0, 0, 1, 1))
    dpi = MagicMock(return_value=42)
    monkeypatch.setattr(
        model_api.preprocessing,
        "convert_figure_bbox_in_points",
        convert,
    )
    monkeypatch.setattr(model_api.preprocessing, "calculate_dpi", dpi)

    images = list(crop_page_images(page_mock, page_dod, ["1"], tmpdir))
    assert images == [
        tmpdir / f"{page_dod.objs[0].idx}.{settings.training_image_format}"
    ]
    assert page_mock.to_image.call_args == call(resolution=42)
    assert convert.call_args == call(
        page_mock.bbox, page_dod.size, page_dod.objs[0].bbox
    )
    assert dpi.call_args == call((0, 0, 1, 1))
