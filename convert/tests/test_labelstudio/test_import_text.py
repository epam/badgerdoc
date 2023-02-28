import pytest

from src.plain_text.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)
from src.text_to_badgerdoc_converter import TextToBadgerdocConverter


def test_correctness_of_import_text_schema(test_app, monkeypatch):
    test_request_payload = {
        "input_text": {"bucket": "test", "path": "1.json"},
        "output_pdf": {"bucket": "test", "path": "2.pdf"},
        "output_tokens": {"bucket": "test", "path": "3.json"},
    }

    def mock_download_text(*args, **kwargs):
        return "1"

    def mock_upload_text(*args, **kwargs):
        pass

    monkeypatch.setattr(
        TextToBadgerdocConverter, "download", mock_download_text
    )
    monkeypatch.setattr(TextToBadgerdocConverter, "upload", mock_upload_text)

    response = test_app.post(
        "/text/import",
        json=(test_request_payload),
    )
    assert response.status_code == 201


def test_import_empty_text():
    converter = TextToBadgerdocTokensConverter()
    converter.convert("")
