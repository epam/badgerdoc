import json

import pytest

from src.labelstudio_to_badgerdoc.badgerdoc_format.badgerdoc_format import (
    BadgerdocFormat,
)
from src.labelstudio_to_badgerdoc.text_to_badgerdoc_converter import (
    TextToBadgerdocConverter,
)


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
        TextToBadgerdocConverter, "download_text_from_s3", mock_download_text
    )
    monkeypatch.setattr(
        TextToBadgerdocConverter, "upload_badgerdoc_to_s3", mock_upload_text
    )

    response = test_app.post(
        "/text/import",
        json=(test_request_payload),
    )
    assert response.status_code == 201


def test_import_empty_text():
    badgerdoc_format = BadgerdocFormat()
    badgerdoc_format.convert_from_text("")
