import json
from pathlib import Path
from tempfile import TemporaryDirectory

from _pytest.monkeypatch import MonkeyPatch
from starlette.testclient import TestClient

from convert.config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from convert.converters.base_format.badgerdoc import Badgerdoc
from convert.converters.labelstudio.labelstudio_to_badgerdoc_converter import (
    ConverterToBadgerdoc,
    LabelstudioToBadgerdocConverter,
)
from convert.converters.labelstudio.models.annotation import LabelStudioModel
from convert.converters.text.text_to_tokens_converter import (
    TextToBadgerdocTokensConverter,
)

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_labelstudio_FILE = TEST_FILES_DIR / "input_text_field.json"
INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "labelstudio_format.json"
BADGERDOC_TOKENS_FILE = TEST_FILES_DIR / "badgerdoc_tokens.json"
TEST_PDF = TEST_FILES_DIR / "test.pdf"


def test_correctness_of_import_text_schema(
    test_app: TestClient, monkeypatch: MonkeyPatch
) -> None:
    test_request_payload = {
        "input_annotation": {
            "bucket": "test",
            "path": "test_converter/ls_format_with_taxonomy.json",
        },
        "output_bucket": "test",
        "validation_type": "cross",
        "deadline": "2024-01-24T11:12:19.549Z",
        "annotators": [
            "a6511931-ddbc-4ea5-a885-5653773d5d48",
            "c2a58313-cffa-4f97-bfcb-dc5aa470f3b7",
        ],
        "validators": [],
    }

    monkeypatch.setattr(
        LabelstudioToBadgerdocConverter,
        "download",
        lambda *args, **kw: LabelStudioModel(),
    )
    monkeypatch.setattr(
        LabelstudioToBadgerdocConverter,
        "upload",
        lambda *args, **kw: ...,
    )
    monkeypatch.setattr(
        LabelstudioToBadgerdocConverter, "execute", lambda *args, **kw: ...
    )
    response = test_app.post(
        "/labelstudio/import",
        json=test_request_payload,
    )

    assert response.status_code == 201


def test_plain_text_converter() -> None:
    labelstudio_data = json.loads(INPUT_labelstudio_FILE.read_text())
    converter = TextToBadgerdocTokensConverter(
        page_width=DEFAULT_PDF_PAGE_WIDTH,
        page_border_offset=DEFAULT_PAGE_BORDER_OFFSET,
        font_height=DEFAULT_PDF_FONT_HEIGHT,
        font_width=DEFAULT_PDF_FONT_WIDTH,
        line_spacing=DEFAULT_PDF_LINE_SPACING,
    )
    tokens = converter.convert(labelstudio_data["text"])
    expected_bd_tokens = json.loads(Path(BADGERDOC_TOKENS_FILE).read_text())
    assert tokens.dict(by_alias=True, exclude_none=True) == expected_bd_tokens


# def test_render_pdf():
#     # TODO write proper comparator
#     tokens = json.loads(Path(BADGERDOC_TOKENS_FILE).read_text())["objs"]
#     bd_tokens = [BadgerdocToken(**token) for token in tokens]
#     with TemporaryDirectory() as dir_name:
#         pdf_file_path = Path(dir_name) / "generated.pdf"
#         PDFRenderer(15).render_tokens(bd_tokens, pdf_file_path)
#         assert (
#             TEST_PDF.read_bytes()[:1500] == pdf_file_path.read_bytes()[:1500]
#         )


def test_annotation_converter() -> None:
    badgerdoc_format = Badgerdoc()
    labelstudio_format = ConverterToBadgerdoc()

    labelstudio_format.to_badgerdoc(
        LabelStudioModel.parse_file(INPUT_LABELSTUDIO_FILE)
    )
    with TemporaryDirectory() as dir_name:
        tokens_test_path = Path(dir_name) / "tokens_test.json"
        annotations_test_path = Path(dir_name) / "annotations_test.json"
        badgerdoc_format.tokens_page = labelstudio_format.tokens_page
        badgerdoc_format.badgerdoc_annotation = (
            labelstudio_format.badgerdoc_annotation
        )
        badgerdoc_format.export_tokens(tokens_test_path)
        badgerdoc_format.export_annotations(annotations_test_path)
        tokens_test = json.loads(tokens_test_path.read_text())
        annotations_test = json.loads(annotations_test_path.read_text())

        tokens_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "tokens_test.json"
        )
        annotations_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "annotations_test.json"
        )
        tokens_etalon = json.loads(tokens_etalon_path.read_text())
        annotations_etalon = json.loads(annotations_etalon_path.read_text())
        assert tokens_test == tokens_etalon
        assert annotations_test == annotations_etalon


def test_import_document_links() -> None:
    badgerdoc_format = Badgerdoc()

    labelstudio_format = ConverterToBadgerdoc()
    labelstudio_format.to_badgerdoc(
        LabelStudioModel.parse_file(INPUT_LABELSTUDIO_FILE)
    )
    badgerdoc_format.tokens_page = labelstudio_format.tokens_page
    badgerdoc_format.badgerdoc_annotation = (
        labelstudio_format.badgerdoc_annotation
    )
    with TemporaryDirectory() as dir_name:
        tokens_test_path = Path(dir_name) / "tokens_test.json"
        annotations_test_path = Path(dir_name) / "annotations_test.json"
        badgerdoc_format.export_tokens(tokens_test_path)
        badgerdoc_format.export_annotations(annotations_test_path)
        tokens_test = json.loads(tokens_test_path.read_text())
        annotations_test = json.loads(annotations_test_path.read_text())

        tokens_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "tokens_test.json"
        )
        annotations_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "annotations_test.json"
        )
        tokens_etalon = json.loads(tokens_etalon_path.read_text())
        annotations_etalon = json.loads(annotations_etalon_path.read_text())
        assert tokens_test == tokens_etalon
        assert annotations_test == annotations_etalon
