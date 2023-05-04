from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from starlette.testclient import TestClient

from convert.converters.labelstudio.labelstudio_to_badgerdoc_converter import (
    LabelstudioToBadgerdocConverter,
)
from convert.converters.labelstudio.models.annotation import LabelStudioModel

TEST_FILES_DIR = Path(__file__).parent / "test_data"

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
        "upload_tokens",
        lambda *args, **kw: ...,
    )
    monkeypatch.setattr(
        LabelstudioToBadgerdocConverter,
        "upload_annotations",
        lambda *args, **kw: ...,
    )
    monkeypatch.setattr(
        LabelstudioToBadgerdocConverter, "execute", lambda *args, **kw: ...
    )
    test_app.headers = {"X-Current-Tenant": "test"}
    response = test_app.post(
        "/labelstudio/import",
        json=test_request_payload,
    )

    assert response.status_code == 201


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
