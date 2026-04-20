import os
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("BADGERDOC_REST_API_RETRY_POLICY", "1,2.0,30,3")
os.environ.setdefault("TEMPORAL_BADGERDOC_ADDRESS", "http://test:8000")
os.environ.setdefault("BADGERDOC_TOKEN", "test_token")
os.environ.setdefault("TEMPORAL_ADDRESS", "localhost:7233")
os.environ.setdefault("BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT", "5")

from badgerdoc_common.activities.document import BadgerdocDocument
from badgerdoc_common.badgerdoc_http import badgerdoc_download


@pytest.mark.asyncio
async def test_badgerdoc_download_success():
    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="/documents/test_file.pdf",
        id=123,
    )

    test_content = b"Test file content for download"

    with patch(
        "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
    ) as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/pdf"}

        async def mock_iter_chunked(chunk_size):
            yield test_content

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()
        await badgerdoc_download(buffer, document)

        assert buffer.getvalue() == test_content
        assert buffer.tell() == 0


@pytest.mark.asyncio
async def test_badgerdoc_download_with_absolute_url():
    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="http://example.com/documents/test_file.pdf",
        id=123,
    )

    test_content = b"Test content"

    with patch(
        "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
    ) as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_iter_chunked(chunk_size):
            yield test_content

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()
        await badgerdoc_download(buffer, document)

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "http://example.com/documents/test_file.pdf"
        assert buffer.getvalue() == test_content


@pytest.mark.asyncio
async def test_badgerdoc_download_with_relative_url():
    from badgerdoc_common import badgerdoc_http

    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="documents/test_file.pdf",
        id=123,
    )

    test_content = b"Test content"

    with (
        patch(
            "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
        ) as mock_session_cls,
        patch.object(
            badgerdoc_http,
            "TEMPORAL_BADGERDOC_ADDRESS",
            "http://badgerdoc:8000",
        ),
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_iter_chunked(chunk_size):
            yield test_content

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()
        await badgerdoc_download(buffer, document)

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert (
            call_args[0][0] == "http://badgerdoc:8000/documents/test_file.pdf"
        )
        assert buffer.getvalue() == test_content


@pytest.mark.asyncio
async def test_badgerdoc_download_with_relative_url_starting_with_slash():
    from badgerdoc_common import badgerdoc_http

    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="/documents/test_file.pdf",
        id=123,
    )

    test_content = b"Test content"

    with (
        patch(
            "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
        ) as mock_session_cls,
        patch.object(
            badgerdoc_http,
            "TEMPORAL_BADGERDOC_ADDRESS",
            "http://badgerdoc:8000",
        ),
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_iter_chunked(chunk_size):
            yield test_content

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()
        await badgerdoc_download(buffer, document)

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert (
            call_args[0][0] == "http://badgerdoc:8000/documents/test_file.pdf"
        )
        assert buffer.getvalue() == test_content


@pytest.mark.asyncio
async def test_badgerdoc_download_clears_buffer():
    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="/documents/test_file.pdf",
        id=123,
    )

    test_content = b"New content"

    with patch(
        "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
    ) as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_iter_chunked(chunk_size):
            yield test_content

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO(b"Old content that should be cleared")
        await badgerdoc_download(buffer, document)

        assert buffer.getvalue() == test_content
        assert b"Old content" not in buffer.getvalue()


@pytest.mark.asyncio
async def test_badgerdoc_download_resets_buffer_position():
    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="/documents/test_file.pdf",
        id=123,
    )

    test_content = b"Test content"

    with patch(
        "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
    ) as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_iter_chunked(chunk_size):
            yield test_content

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()
        await badgerdoc_download(buffer, document)

        assert buffer.tell() == 0


@pytest.mark.asyncio
async def test_badgerdoc_download_large_file_chunked():
    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="/documents/test_file.pdf",
        id=123,
    )

    chunk1 = b"x" * 8192
    chunk2 = b"y" * 4096
    expected_content = chunk1 + chunk2

    with patch(
        "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
    ) as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_iter_chunked(chunk_size):
            assert chunk_size == 8192
            yield chunk1
            yield chunk2

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()
        await badgerdoc_download(buffer, document)

        assert buffer.getvalue() == expected_content
        assert len(buffer.getvalue()) == 12288


@pytest.mark.asyncio
async def test_badgerdoc_download_missing_file_url():
    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file=None,
        id=123,
    )

    buffer = BytesIO()

    with pytest.raises(ValueError, match="Document file URL is required"):
        await badgerdoc_download(buffer, document)


@pytest.mark.asyncio
async def test_badgerdoc_download_empty_file_url():
    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="",
        id=123,
    )

    buffer = BytesIO()

    with pytest.raises(ValueError, match="Document file URL is required"):
        await badgerdoc_download(buffer, document)


@pytest.mark.asyncio
async def test_badgerdoc_download_http_error():
    import aiohttp

    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="/documents/test_file.pdf",
        id=123,
    )

    with patch(
        "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
    ) as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Not found")
        mock_response.request_info = MagicMock()
        mock_response.history = []

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()

        with pytest.raises(aiohttp.ClientResponseError) as exc_info:
            await badgerdoc_download(buffer, document)

        assert exc_info.value.status == 404


@pytest.mark.asyncio
async def test_badgerdoc_download_includes_authorization_header():
    from badgerdoc_common import badgerdoc_http

    document = BadgerdocDocument(
        name="test_document",
        extension="pdf",
        file="/documents/test_file.pdf",
        id=123,
    )

    test_content = b"Test content"

    with (
        patch(
            "badgerdoc_common.badgerdoc_http.aiohttp.ClientSession"
        ) as mock_session_cls,
        patch.object(badgerdoc_http, "BADGERDOC_TOKEN", "test_token_123"),
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_iter_chunked(chunk_size):
            yield test_content

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        mock_session.get.return_value = mock_get_ctx

        buffer = BytesIO()
        await badgerdoc_download(buffer, document)

        mock_session.get.assert_called_once()
        call_kwargs = mock_session.get.call_args[1]
        assert "headers" in call_kwargs
        assert (
            call_kwargs["headers"]["Authorization"] == "Token test_token_123"
        )
