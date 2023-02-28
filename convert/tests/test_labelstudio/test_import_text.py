import pytest

from src.plain_text.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)
from src.text_to_badgerdoc_converter import TextToBadgerdocConverter


def test_correctness_of_import_text_schema(test_app, monkeypatch) -> None:
    test_request_payload = {
        "input_text": {"bucket": "test", "path": "1.json"},
        "output_pdf": {"bucket": "test", "path": "2.pdf"},
        "output_tokens": {"bucket": "test", "path": "3.json"},
    }

    monkeypatch.setattr(
        TextToBadgerdocConverter, "download", lambda *args, **kw: "1"
    )
    monkeypatch.setattr(TextToBadgerdocConverter, "upload",  lambda *args, **kw: ...)

    response = test_app.post(
        "/text/import",
        json=(test_request_payload),
    )
    assert response.status_code == 201


def test_import_empty_text() -> None:
    converter = TextToBadgerdocTokensConverter()
    converter.convert("")
