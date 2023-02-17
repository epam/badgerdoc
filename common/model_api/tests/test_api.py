import pytest

from pathlib import Path
from unittest.mock import MagicMock

import model_api.pipeline
from model_api.common import models as m
from model_api.utils import (
    update_annotation_categories,
    form_response,
    get_needs_from_request_and_annotation,
)

# from model_api.inference import inference


@pytest.mark.skip(
    reason="this is a test from a different, but similar service"
)
def test_inference(monkeypatch):
    model_mock = MagicMock()
    monkeypatch.setattr(
        model_api.inference, "open_image", lambda x: "0"
    )  # 0 is a class number
    model_mock.predict = lambda class_number: (class_number, "other_variant")
    model_mock.data.classes = (
        "chart",
        "molecule",
        "other",
    )
    image = Path("/path/name.png")
    image_name, category = list(inference(model_mock, [image]))[0]
    assert image_name == "name.png"
    assert category == "chart"


def test_update_annotation_categories_updating(monkeypatch):
    page_dod = m.PageDOD(
        page_num=1,
        size=m.Size(width=2550, height=3300),
        objs=[
            m.GeometryObject(
                id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                bbox=(1321, 2004, 2339, 2631),
                category="0",
            ),
            m.GeometryObject(
                id="732f2735-3369-4305-9d29-fa3be99d72dd",
                bbox=(1276, 1114, 2356, 1621),
                category="3",
            ),
        ],
    )
    monkeypatch.setattr(model_api.utils, "crop_page_images", MagicMock())
    inference = MagicMock(
        return_value=[
            (
                "732f2735-3369-4305-9d29-fa3be99d72dd.png",
                {"data": {"chemical_formula": "31"}},
            )
        ]
    )
    pdf = MagicMock()
    setattr(pdf, "pages", [1])
    update_annotation_categories(
        inference, None, page_dod, pdf, ["1", "3"], ...
    )

    assert page_dod == m.PageDOD(
        page_num=1,
        size=m.Size(width=2550, height=3300),
        objs=[
            m.GeometryObject(
                id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                bbox=(1321, 2004, 2339, 2631),
                category="0",
            ),
            m.GeometryObject(
                id="732f2735-3369-4305-9d29-fa3be99d72dd",
                bbox=(1276, 1114, 2356, 1621),
                category="3",
                data={"chemical_formula": "31"},
            ),
        ],
    )


def test_update_annotation_categories_without_updating(monkeypatch):
    page_dod = m.PageDOD(
        page_num=1,
        size=m.Size(width=2550, height=3300),
        objs=[
            m.GeometryObject(
                id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                bbox=(1321, 2004, 2339, 2631),
                category="0",
            ),
            m.GeometryObject(
                id="732f2735-3369-4305-9d29-fa3be99d72dd",
                bbox=(1276, 1114, 2356, 1621),
                category="3",
            ),
        ],
    )
    monkeypatch.setattr(model_api.utils, "crop_page_images", MagicMock())
    inference = MagicMock(return_value=[])
    pdf = MagicMock()
    setattr(pdf, "pages", [1])
    update_annotation_categories(
        inference, None, page_dod, pdf, ["1", "3"], ...
    )

    assert page_dod == m.PageDOD(
        page_num=1,
        size=m.Size(width=2550, height=3300),
        objs=[
            m.GeometryObject(
                id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                bbox=(1321, 2004, 2339, 2631),
                category="0",
            ),
            m.GeometryObject(
                id="732f2735-3369-4305-9d29-fa3be99d72dd",
                bbox=(1276, 1114, 2356, 1621),
                category="3",
            ),
        ],
    )


def test_update_annotation_categories_only_several_ids(monkeypatch):
    page_dod = m.PageDOD(
        page_num=1,
        size=m.Size(width=2550, height=3300),
        objs=[
            m.GeometryObject(
                id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                bbox=(1321, 2004, 2339, 2631),
                category="3",
            ),
            m.GeometryObject(
                id="732f2735-3369-4305-9d29-fa3be99d72dd",
                bbox=(1276, 1114, 2356, 1621),
                category="3",
            ),
        ],
    )
    monkeypatch.setattr(model_api.utils, "crop_page_images", MagicMock())
    inference = MagicMock(
        return_value=[
            (
                "aab83828-cd8b-41f7-a3c3-943f13e67c2c.png",
                {"data": {"chemical_formula": "some_value"}},
            ),
            (
                "732f2735-3369-4305-9d29-fa3be99d72dd.png",
                {"data": {"chemical_formula": "31"}},
            ),
        ]
    )
    pdf = MagicMock()
    setattr(pdf, "pages", [1])
    update_annotation_categories(
        inference,
        None,
        page_dod,
        pdf,
        ["1", "3"],
        None,
        tuple(("732f2735-3369-4305-9d29-fa3be99d72dd",)),
    )

    assert page_dod == m.PageDOD(
        page_num=1,
        size=m.Size(width=2550, height=3300),
        objs=[
            m.GeometryObject(
                id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                bbox=(1321, 2004, 2339, 2631),
                category="3",
            ),
            m.GeometryObject(
                id="732f2735-3369-4305-9d29-fa3be99d72dd",
                bbox=(1276, 1114, 2356, 1621),
                category="3",
                data={"chemical_formula": "31"},
            ),
        ],
    )


def test_form_response():
    dod_pages = [
        m.PageDOD(
            page_num=1,
            size=m.Size(width=2550, height=3300),
            objs=[
                m.GeometryObject(
                    id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                    bbox=(1321, 2004, 2339, 2631),
                    category="10",
                ),
                m.GeometryObject(
                    id="732f2735-3369-4305-9d29-fa3be99d72dd",
                    bbox=(1276, 1114, 2356, 1621),
                    category="31",
                ),
            ],
        )
    ]
    input_field = {
        "0": {"1": ["30e4d539-8e90-49c7-b49c-883073e2b8c8"]},
        "3": {
            "1": ["aab83828-cd8b-41f7-a3c3-943f13e67c2c"],
            "2": [
                "44d94e31-7079-470a-b8b5-74ce365353f7",
                "d86d467f-6ec1-404e-b4e6-ba8d78f93754",
            ],
        },
    }
    result = form_response(dod_pages, input_field)
    assert result == {
        "0": {"1": ["30e4d539-8e90-49c7-b49c-883073e2b8c8"]},
        "10": {"1": ["aab83828-cd8b-41f7-a3c3-943f13e67c2c"]},
        "3": {
            "2": [
                "44d94e31-7079-470a-b8b5-74ce365353f7",
                "d86d467f-6ec1-404e-b4e6-ba8d78f93754",
            ]
        },
    }


def test_get_needs_from_request_and_annotation():
    dod_pages = [
        m.PageDOD(
            page_num=1,
            size=m.Size(width=2550, height=3300),
            objs=[
                m.GeometryObject(
                    id="aab83828-cd8b-41f7-a3c3-943f13e67c21",
                    bbox=(1321, 2004, 2339, 2631),
                    category="1",
                ),
                m.GeometryObject(
                    id="732f2735-3369-4305-9d29-fa3be99d72d2",
                    bbox=(1276, 1114, 2356, 1621),
                    category="2",
                ),
            ],
        ),
        m.PageDOD(
            page_num=2,
            size=m.Size(width=2550, height=3300),
            objs=[
                m.GeometryObject(
                    id="aab83828-cd8b-41f7-a3c3-943f13e67c23",
                    bbox=(1321, 2004, 2339, 2631),
                    category="3",
                ),
                m.GeometryObject(
                    id="732f2735-3369-4305-9d29-fa3be99d72d4",
                    bbox=(1276, 1114, 2356, 1621),
                    category="4",
                ),
            ],
        ),
    ]
    input_field = {
        "3": {
            "2": [
                "aab83828-cd8b-41f7-a3c3-943f13e67c23",
            ],
        },
    }
    needed_pages, obj_ids = get_needs_from_request_and_annotation(
        dod_pages, input_field
    )
    assert list(needed_pages) == [
        m.PageDOD(
            page_num=2,
            size=m.Size(width=2550, height=3300),
            objs=[
                m.GeometryObject(
                    id="aab83828-cd8b-41f7-a3c3-943f13e67c23",
                    bbox=(1321, 2004, 2339, 2631),
                    category="3",
                ),
                m.GeometryObject(
                    id="732f2735-3369-4305-9d29-fa3be99d72d4",
                    bbox=(1276, 1114, 2356, 1621),
                    category="4",
                ),
            ],
        ),
    ]
    assert list(obj_ids) == [
        "aab83828-cd8b-41f7-a3c3-943f13e67c23",
    ]
