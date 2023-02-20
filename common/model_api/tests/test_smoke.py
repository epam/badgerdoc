from pathlib import Path
from pprint import pprint
from unittest.mock import MagicMock

import model_api
import pytest
from model_api.common import models as m
from model_api.pipeline import pipeline

annotation_from_minio = m.AnnotationFromS3(
    pages=[
        m.PageDOD(
            page_num=1,
            size=m.Size(width=2550, height=3300),
            objs=[
                m.GeometryObject(
                    id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
                    bbox=(1321, 2004, 2339, 2631),
                    category="3",
                ),
                m.GeometryObject(
                    id="30e4d539-8e90-49c7-b49c-883073e2b8c8",
                    bbox=(223, 2590, 1234, 2875),
                    category="0",
                ),
                m.GeometryObject(
                    id="df4e3a06-09ac-485c-bf12-ecebd14e7f74",
                    bbox=(237, 2364, 1226, 2448),
                    category="3",
                ),
                m.GeometryObject(
                    id="bf7344d0-3a1e-401f-b802-6236620cc01e",
                    bbox=(1318, 1690, 2328, 1859),
                    category="3",
                ),
                m.GeometryObject(
                    id="732f2735-3369-4305-9d29-fa3be99d72dd",
                    bbox=(1276, 1114, 2356, 1621),
                    category="3",
                ),
            ],
        ),
        m.PageDOD(
            page_num=5,
            size=m.Size(width=2550, height=3300),
            objs=[
                m.GeometryObject(
                    id="44d94e31-7079-470a-b8b5-74ce365353f7",
                    bbox=(1316, 2452, 2333, 2966),
                    category="0",
                ),
                m.GeometryObject(
                    id="ab1847e2-020d-453d-a218-3ac239ec5810",
                    bbox=(1330, 809, 2330, 1641),
                    category="0",
                ),
                m.GeometryObject(
                    id="7a4a2251-1263-4f52-a13b-fddf6b6f3bd1",
                    bbox=(230, 1695, 1226, 1914),
                    category="0",
                ),
                m.GeometryObject(
                    id="d86d467f-6ec1-404e-b4e6-ba8d78f93754",
                    bbox=(217, 399, 1225, 1589),
                    category="3",
                ),
            ],
        ),
    ]
)
request = m.ClassifierRequest(
    input_path=Path("ternary_out/molecule_annotation.json"),
    input={
        "0": {"1": ["30e4d539-8e90-49c7-b49c-883073e2b8c8"]},
        "3": {
            "1": ["aab83828-cd8b-41f7-a3c3-943f13e67c2c"],
            "2": [
                "44d94e31-7079-470a-b8b5-74ce365353f7",
                "d86d467f-6ec1-404e-b4e6-ba8d78f93754",
            ],
        },
    },
    file=Path("molecule.pdf"),
    bucket="annotation",
    output_path=Path("ternary_out/molecule_annotation_out.json"),
    output_bucket="annotation",
    args=m.Args(categories=["1", "3"]),
)


class MockPDF:
    class PDF:
        pages: list = [1, 2, 3]

    def __enter__(self):
        return self.PDF()

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


def inference_return(model, images):
    for image in images:
        if image == Path("aab83828-cd8b-41f7-a3c3-943f13e67c2c.png"):
            print("inference yield 1")
            yield "aab83828-cd8b-41f7-a3c3-943f13e67c2c", {
                "chemical_formula": "31"
            }

        if image == Path("732f2735-3369-4305-9d29-fa3be99d72dd.png"):
            print("inference yield 2")
            yield "732f2735-3369-4305-9d29-fa3be99d72dd", {
                "chemical_formula": "31"
            }


def crop_page_return(pdf_page, dod_page: m.PageDOD, categories, output_path):
    if dod_page.page_num == 1:
        print("crop_page yield 1")
        yield Path("aab83828-cd8b-41f7-a3c3-943f13e67c2c.png")
        print("crop_page yield 2")
        yield Path("732f2735-3369-4305-9d29-fa3be99d72dd.png")


def mock_put_annotation(loader, work_dir, annotation, request):
    print(annotation)


# annotation_to_minio = m.AnnotationFromS3(
#     pages=[
#         m.PageDOD(
#             page_num=1,
#             size=m.Size(width=2550, height=3300),
#             objs=[
#                 m.GeometryObject(
#                     id="aab83828-cd8b-41f7-a3c3-943f13e67c2c",
#                     bbox=(1321, 2004, 2339, 2631),
#                     category="0",
#                 ),
#                 m.GeometryObject(
#                     id="30e4d539-8e90-49c7-b49c-883073e2b8c8",
#                     bbox=(223, 2590, 1234, 2875),
#                     category="0",
#                 ),
#                 m.GeometryObject(
#                     id="df4e3a06-09ac-485c-bf12-ecebd14e7f74",
#                     bbox=(237, 2364, 1226, 2448),
#                     category="31",
#                 ),
#                 m.GeometryObject(
#                     id="bf7344d0-3a1e-401f-b802-6236620cc01e",
#                     bbox=(1318, 1690, 2328, 1859),
#                     category="0",
#                 ),
#                 m.GeometryObject(
#                     id="732f2735-3369-4305-9d29-fa3be99d72dd",
#                     bbox=(1276, 1114, 2356, 1621),
#                     category="31",
#                 ),
#             ],
#         ),
#         m.PageDOD(
#             page_num=5,
#             size=m.Size(width=2550, height=3300),
#             objs=[
#                 m.GeometryObject(
#                     id="44d94e31-7079-470a-b8b5-74ce365353f7",
#                     bbox=(1316, 2452, 2333, 2966),
#                     category="0",
#                 ),
#                 m.GeometryObject(
#                     id="ab1847e2-020d-453d-a218-3ac239ec5810",
#                     bbox=(1330, 809, 2330, 1641),
#                     category="0",
#                 ),
#                 m.GeometryObject(
#                     id="7a4a2251-1263-4f52-a13b-fddf6b6f3bd1",
#                     bbox=(230, 1695, 1226, 1914),
#                     category="0",
#                 ),
#                 m.GeometryObject(
#                     id="d86d467f-6ec1-404e-b4e6-ba8d78f93754",
#                     bbox=(217, 399, 1225, 1589),
#                     category="3",
#                 ),
#             ],
#         ),
#     ]
# )
response = {
    "0": {
        "1": [
            "30e4d539-8e90-49c7-b49c-883073e2b8c8",
            "aab83828-cd8b-41f7-a3c3-943f13e67c2c",
        ]
    },
    "3": {
        "2": [
            "44d94e31-7079-470a-b8b5-74ce365353f7",
            "d86d467f-6ec1-404e-b4e6-ba8d78f93754",
        ]
    },
}


@pytest.mark.skip(
    reason="test data are far-fetched. "
    "But the program should be modified "
    "in the future."
)
def test_form_response(monkeypatch):
    monkeypatch.setattr(
        model_api.pipeline,
        "get_document",
        MagicMock(return_value=""),
    )
    monkeypatch.setattr(
        model_api.pipeline,
        "get_annotation",
        MagicMock(return_value=annotation_from_minio.pages),
    )
    monkeypatch.setattr(
        model_api.pipeline.pdfplumber,
        "open",
        MagicMock(return_value=MockPDF()),
    )
    monkeypatch.setattr(
        model_api.pipeline,
        "crop_page_images",
        crop_page_return,
    )
    # monkeypatch.setattr(
    #     model_api.pipeline, "inference", inference_return
    # )
    monkeypatch.setattr(
        model_api.pipeline,
        "put_annotation",
        mock_put_annotation,
    )

    inference_and_save_result = pipeline(
        get_model=(lambda: None),
        inference=inference_return,
        request=request,
        loader=None,
        work_dir=None,
    )
    assert m.ClassifierResponse(__root__=response) == inference_and_save_result
