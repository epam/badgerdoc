from unittest.mock import patch

from processing.schema import (
    AnnotationData,
    MatchedPage,
    Page,
    ParagraphBbox,
    PageSize,
    Input,
)
from processing.text_merge import (
    convert_points_to_pixels,
    match_page,
    download_files,
    stitch_boxes,
)


class ClientObj:
    def __init__(self, name):
        self.object_name = name


class Client:
    def fget_object(self, *args, **kwargs):
        pass

    def list_objects(self, *args, **kwargs):
        return [ClientObj("ocr/1.png"), ClientObj("ocr/2.png")]


class MC:
    def __init__(self):
        self.client = Client()


class TestTextMerger:
    def test_match_page(self):
        words = {
            "size": {"width": 595.276, "height": 841.89},
            "page_num": 1,
            "objs": [{"type": "text", "bbox": (3, 3, 8, 8), "text": "1 2 3"}],
        }
        page = Page(
            page_num=1,
            size=PageSize(width=1000, height=1000),
            objs=[
                {"id": 1, "bbox": [1, 1, 10, 10], "category": "1", "text": ""},
                {
                    "id": 2,
                    "bbox": [100, 100, 110, 110],
                    "category": "1",
                    "text": "",
                },
            ],
        )
        assert match_page(words=words, page=page) == MatchedPage(
            page_num=1,
            paragraph_bboxes={
                1: ParagraphBbox(
                    bbox=[1, 1, 10, 10],
                    nested_bboxes=[
                        {"x1": 3, "y1": 3, "x2": 8, "y2": 8, "text": "1 2 3"}
                    ],
                )
            },
        )

    def test_match_empty_annotations(self):
        words = {
            "size": {"width": 595.276, "height": 841.89},
            "page": 1,
            "objs": [
                {"type": "text", "bbox": (3, 3, 8, 8), "text": "1 2 3"},
            ],
        }
        page = Page(
            page_num=1, size=PageSize(width=1000, height=1000), objs=[]
        )
        assert match_page(words=words, page=page) == MatchedPage(
            page_num=1, paragraph_bboxes={}
        )

    def test_match_empty_words(self):
        words = {
            "size": {"width": 595.276, "height": 841.89},
            "page_num": 1,
            "objs": [],
        }
        page = Page(
            page_num=1,
            size=PageSize(width=1000, height=1000),
            objs=[
                {"id": 1, "bbox": [1, 1, 10, 10], "category": "1", "text": ""},
                {
                    "id": 2,
                    "bbox": [100, 100, 110, 110],
                    "category": "1",
                    "text": "",
                },
            ],
        )
        assert match_page(words=words, page=page) == MatchedPage(
            page_num=1, paragraph_bboxes={}
        )

    def test_convert_points_to_pixels(self):
        old_page = {
            "size": {"width": 100, "height": 100},
            "page_num": 1,
            "objs": [
                {"type": "text", "bbox": [10, 10, 20, 20], "text": "1 2 3"},
            ],
        }
        new_page = convert_points_to_pixels(old_page, 200, 200)
        assert new_page["objs"][0]["bbox"][0] == 20
        assert new_page["objs"][0]["bbox"][1] == 20
        assert new_page["objs"][0]["bbox"][2] == 40
        assert new_page["objs"][0]["bbox"][3] == 40

    def test_stitch_boxes(self):
        matched_pages = [
            MatchedPage(
                page_num=1,
                paragraph_bboxes={
                    1: ParagraphBbox(
                        bbox=(1, 1, 10, 10),
                        nested_bboxes=[
                            {
                                "x1": 3,
                                "y1": 3,
                                "x2": 8,
                                "y2": 8,
                                "text": "1 2 3",
                            },
                            {
                                "x1": 10,
                                "y1": 3,
                                "x2": 13,
                                "y2": 8,
                                "text": "4 5 6",
                            },
                        ],
                    )
                },
            )
        ]
        annotations = [
            Page(
                page_num=1,
                size=PageSize(width=1000, height=1000),
                objs=[
                    {
                        "id": 1,
                        "bbox": [0, 0, 101, 101],
                        "category": "1",
                        "text": "",
                    },
                    {
                        "id": 2,
                        "bbox": [200, 200, 300, 300],
                        "category": "1",
                        "text": "",
                    },
                ],
            ),
            Page(
                page_num=2,
                size=PageSize(width=1000, height=1000),
                objs=[
                    {
                        "id": 1,
                        "bbox": [0, 0, 101, 101],
                        "category": "1",
                        "text": "",
                    },
                    {
                        "id": 2,
                        "bbox": [200, 200, 300, 300],
                        "category": "1",
                        "text": "",
                    },
                ],
            ),
        ]
        stitch_boxes(matched_pages, annotations)
        assert annotations == [
            Page(
                page_num=1,
                size=PageSize(width=1000, height=1000),
                objs=[
                    {
                        "id": 1,
                        "bbox": [0, 0, 101, 101],
                        "category": "1",
                        "text": "1 2 3 4 5 6",
                    },
                    {
                        "id": 2,
                        "bbox": [200, 200, 300, 300],
                        "category": "1",
                        "text": "",
                    },
                ],
            ),
            Page(
                page_num=2,
                size=PageSize(width=1000, height=1000),
                objs=[
                    {
                        "id": 1,
                        "bbox": [0, 0, 101, 101],
                        "category": "1",
                        "text": "",
                    },
                    {
                        "id": 2,
                        "bbox": [200, 200, 300, 300],
                        "category": "1",
                        "text": "",
                    },
                ],
            ),
        ]

    @patch("processing.text_merge.MinioCommunicator", return_value=MC())
    def test_download(self, _1, tmp_path):
        request_data = AnnotationData(
            file="some_path/some_file.pdf",
            bucket="some_bucket",
            input=Input(
                pages=[
                    Page(
                        page_num=1, size=PageSize(width=10, height=10), objs=[]
                    ),
                    Page(
                        page_num=2, size=PageSize(width=10, height=10), objs=[]
                    ),
                ]
            ),
        )

        assert download_files(request_data, tmp_path) == tmp_path / "ocr"
