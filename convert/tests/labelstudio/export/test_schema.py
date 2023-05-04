from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from starlette.testclient import TestClient

from convert.converters.labelstudio.badgerdoc_to_labelstudio_converter import (
    BadgerdocToLabelstudioConverter,
)

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "labelstudio_format.json"


def test_correctness_of_export_text_schema(
    test_app: TestClient, monkeypatch: MonkeyPatch
) -> None:
    test_request_payload = {
        "input_tokens": {"bucket": "test", "path": "files/926/ocr/1.json"},
        "input_annotation": {
            "bucket": "test",
            "path": "annotation/1763/926/"
            "1ae7876fd4d777d5b4e6dbd338b230d74aa4ff8d.json",
        },
        "input_manifest": {
            "bucket": "test",
            "path": "annotation/1763/926/manifest.json",
        },
        "output_annotation": {
            "bucket": "test",
            "path": "test_converter/out.json",
        },
    }

    monkeypatch.setattr(
        BadgerdocToLabelstudioConverter, "execute", lambda *args, **kw: ...
    )

    test_app.headers = {"X-Current-Tenant": "test"}
    response = test_app.post(
        "/labelstudio/export",
        json=test_request_payload,
    )

    assert response.status_code == 201
