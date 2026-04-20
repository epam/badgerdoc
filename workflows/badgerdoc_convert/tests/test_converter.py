from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from badgerdoc_convert.activities.pdf import download_and_convert_document


@pytest.mark.asyncio
async def test_download_and_convert_document():
    document_id = 123
    fake_document = MagicMock()
    fake_document.metadata = {"author": "test"}

    # Mock badgerdoc_get_document
    with (
        patch(
            "badgerdoc_convert.activities.pdf.badgerdoc_get_document",
            new=AsyncMock(return_value=fake_document),
        ) as mock_get_doc,
        patch(
            "badgerdoc_convert.activities.pdf.badgerdoc_http.badgerdoc_download",
            new=AsyncMock(),
        ) as mock_download,
        patch(
            "badgerdoc_convert.activities.pdf.badgerdoc_http.badgerdoc_upload",
            new=AsyncMock(return_value={"id": "img123"}),
        ) as mock_upload,
        patch(
            "badgerdoc_convert.activities.pdf.badgerdoc_list_documents",
            new=AsyncMock(return_value=MagicMock(documents=[])),
        ) as mock_list_docs,
        patch(
            "badgerdoc_convert.activities.pdf.badgerdoc_delete_document",
            new=AsyncMock(),
        ) as mock_delete_doc,
        patch("pdfplumber.open") as mock_pdf_open,
    ):

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_image = MagicMock()
        mock_image.original = MagicMock()

        def fake_save(buffer, format):
            buffer.write(b"fakeimage")

        mock_image.original.save.side_effect = fake_save
        mock_page.to_image.return_value = mock_image
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        result = await download_and_convert_document(document_id)

        mock_get_doc.assert_awaited_once_with(document_id)
        mock_list_docs.assert_awaited_once()
        mock_download.assert_awaited_once()
        mock_pdf_open.assert_called_once()
        mock_upload.assert_awaited_once()

        assert result.pages_converted == 1
        assert result.pages_statuses == [True]
