import pytest
from _pytest.monkeypatch import MonkeyPatch
from starlette.testclient import TestClient

from src.converters.text.text_to_badgerdoc_converter import (
    TextToBadgerdocConverter,
)
from src.converters.text.text_to_tokens_converter import (
    TextToBadgerdocTokensConverter,
)


def test_correctness_of_import_text_schema(
    test_app: TestClient, monkeypatch: MonkeyPatch
) -> None:
    test_request_payload = {
        "input_text": {"bucket": "test", "path": "1.json"},
        "output_pdf": {"bucket": "test", "path": "2.pdf"},
        "output_tokens": {"bucket": "test", "path": "3.json"},
    }

    monkeypatch.setattr(
        TextToBadgerdocConverter, "download", lambda *args, **kw: "1"
    )
    monkeypatch.setattr(
        TextToBadgerdocConverter, "upload", lambda *args, **kw: ...
    )

    response = test_app.post(
        "/text/import",
        json=(test_request_payload),
    )
    assert response.status_code == 201


def test_import_empty_text() -> None:
    converter = TextToBadgerdocTokensConverter()
    converter.convert("")
