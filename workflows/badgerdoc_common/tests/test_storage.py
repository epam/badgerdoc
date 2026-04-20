import os
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest

os.environ.setdefault("BADGERDOC_REST_API_RETRY_POLICY", "1,2.0,30,3")
os.environ.setdefault("TEMPORAL_BADGERDOC_ADDRESS", "http://test:8000")
os.environ.setdefault("BADGERDOC_TOKEN", "test_token")
os.environ.setdefault("TEMPORAL_ADDRESS", "localhost:7233")
os.environ.setdefault("BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT", "5")
os.environ.setdefault("BADGERDOC_OBJECT_STORAGE_BUCKET", "test-bucket")
os.environ.setdefault("BADGERDOC_OBJECT_STORAGE_ACCESS_KEY", "test-key")
os.environ.setdefault("BADGERDOC_OBJECT_STORAGE_SECRET_KEY", "test-secret")
os.environ.setdefault("BADGERDOC_OBJECT_STORAGE_URL", "http://localhost:9000")
os.environ.setdefault("BADGERDOC_OBJECT_STORAGE_REGION", "us-east-1")
os.environ.setdefault("BADGERDOC_OBJECT_STORAGE_ADDRESSING_STYLE", "path")

from badgerdoc_common.storage import (
    StorageWorkflowParams,
    badgerdoc_download_perm,
    badgerdoc_download_temp,
    badgerdoc_store_perm,
    badgerdoc_store_temp,
)


@pytest.mark.asyncio
async def test_badgerdoc_store_temp_with_filename():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO(b"Test content")
    filename = "test_file.txt"

    with patch("badgerdoc_common.storage.badgerdoc_store") as mock_upload:
        result = await badgerdoc_store_temp(buffer, params, filename)

        expected_path = "tmp/workflows/test_workflow/TestWorkflow/workflow-123/test_file.txt"
        assert result == expected_path
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args[0][1] == expected_path


@pytest.mark.asyncio
async def test_badgerdoc_store_temp_without_filename():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO(b"Test content")
    filename = "test-uuid-hex"

    with patch("badgerdoc_common.storage.badgerdoc_store") as mock_upload:
        result = await badgerdoc_store_temp(buffer, params, filename)

        expected_path = "tmp/workflows/test_workflow/TestWorkflow/workflow-123/test-uuid-hex"
        assert result == expected_path
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args[0][1] == expected_path


@pytest.mark.asyncio
async def test_badgerdoc_store_temp_resets_buffer():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO(b"Test content")
    buffer.seek(5)

    with patch("badgerdoc_common.storage.badgerdoc_store") as mock_upload:
        await badgerdoc_store_temp(buffer, params, "test.txt")

        call_args = mock_upload.call_args
        assert call_args[0][0].getvalue() == b"Test content"


@pytest.mark.asyncio
async def test_badgerdoc_store_temp_missing_bucket():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO(b"Test content")

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("BADGERDOC_OBJECT_STORAGE_BUCKET", None)
        with pytest.raises(ValueError, match="Bucket name is required"):
            await badgerdoc_store_temp(buffer, params, "test.txt")


@pytest.mark.asyncio
async def test_badgerdoc_store_perm_with_filename():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO(b"Test content")
    filename = "test_file.txt"

    with patch("badgerdoc_common.storage.badgerdoc_store") as mock_upload:
        result = await badgerdoc_store_perm(buffer, params, filename)

        expected_path = "data/workflows/test_workflow/TestWorkflow/workflow-123/test_file.txt"
        assert result == expected_path
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args[0][1] == expected_path


@pytest.mark.asyncio
async def test_badgerdoc_store_perm_without_filename():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO(b"Test content")
    filename = "test-uuid-hex"

    with patch("badgerdoc_common.storage.badgerdoc_store") as mock_upload:
        result = await badgerdoc_store_perm(buffer, params, filename)

        expected_path = "data/workflows/test_workflow/TestWorkflow/workflow-123/test-uuid-hex"
        assert result == expected_path
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args[0][1] == expected_path


@pytest.mark.asyncio
async def test_badgerdoc_store_perm_missing_bucket():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO(b"Test content")

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("BADGERDOC_OBJECT_STORAGE_BUCKET", None)
        with pytest.raises(ValueError, match="Bucket name is required"):
            await badgerdoc_store_perm(buffer, params, "test.txt")


@pytest.mark.asyncio
async def test_badgerdoc_download_temp_success():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    path = "tmp/workflows/test_workflow/TestWorkflow/workflow-123/test.txt"
    test_content = b"Test file content"
    buffer = BytesIO(b"existing content")

    with patch("badgerdoc_common.storage._get_s3_client") as mock_get_client:
        mock_s3_client = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_get_client.return_value.__aexit__.return_value = None

        async def mock_chunks():
            yield test_content

        mock_body = mock_chunks()
        mock_response = {"Body": mock_body}
        mock_s3_client.get_object = AsyncMock(return_value=mock_response)

        await badgerdoc_download_temp(buffer, params, "test.txt")

        assert buffer.getvalue() == test_content
        assert buffer.tell() == 0
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key=path
        )


@pytest.mark.asyncio
async def test_badgerdoc_download_temp_clears_buffer():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    test_content = b"New content"
    buffer = BytesIO(b"Old content that should be cleared")

    with patch("badgerdoc_common.storage._get_s3_client") as mock_get_client:
        mock_s3_client = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_get_client.return_value.__aexit__.return_value = None

        async def mock_chunks():
            yield test_content

        mock_body = mock_chunks()
        mock_response = {"Body": mock_body}
        mock_s3_client.get_object = AsyncMock(return_value=mock_response)

        await badgerdoc_download_temp(buffer, params, "test.txt")

        assert buffer.getvalue() == test_content
        assert "Old content" not in buffer.getvalue().decode(
            "utf-8", errors="ignore"
        )


@pytest.mark.asyncio
async def test_badgerdoc_download_temp_resets_position():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    test_content = b"Test content"
    buffer = BytesIO(test_content)
    buffer.seek(10)

    with patch("badgerdoc_common.storage._get_s3_client") as mock_get_client:
        mock_s3_client = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_get_client.return_value.__aexit__.return_value = None

        async def mock_chunks():
            yield test_content

        mock_body = mock_chunks()
        mock_response = {"Body": mock_body}
        mock_s3_client.get_object = AsyncMock(return_value=mock_response)

        await badgerdoc_download_temp(buffer, params, "test.txt")

        assert buffer.tell() == 0


@pytest.mark.asyncio
async def test_badgerdoc_download_temp_missing_bucket():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    buffer = BytesIO()

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("BADGERDOC_OBJECT_STORAGE_BUCKET", None)
        with pytest.raises(ValueError, match="Bucket name is required"):
            await badgerdoc_download_temp(buffer, params, "test.txt")


@pytest.mark.asyncio
async def test_badgerdoc_download_temp_large_file():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    chunk1 = b"Chunk 1 " * 1000
    chunk2 = b"Chunk 2 " * 1000
    buffer = BytesIO()

    with patch("badgerdoc_common.storage._get_s3_client") as mock_get_client:
        mock_s3_client = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_get_client.return_value.__aexit__.return_value = None

        async def mock_chunks():
            yield chunk1
            yield chunk2

        mock_body = mock_chunks()
        mock_response = {"Body": mock_body}
        mock_s3_client.get_object = AsyncMock(return_value=mock_response)

        await badgerdoc_download_temp(buffer, params, "test.txt")

        expected_content = chunk1 + chunk2
        assert buffer.getvalue() == expected_content


@pytest.mark.asyncio
async def test_badgerdoc_download_perm_success():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    path = "data/workflows/test_workflow/TestWorkflow/workflow-123/test.txt"
    test_content = b"Test file content"
    buffer = BytesIO()

    with patch("badgerdoc_common.storage._get_s3_client") as mock_get_client:
        mock_s3_client = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_get_client.return_value.__aexit__.return_value = None

        async def mock_chunks():
            yield test_content

        mock_body = mock_chunks()
        mock_response = {"Body": mock_body}
        mock_s3_client.get_object = AsyncMock(return_value=mock_response)

        await badgerdoc_download_perm(buffer, params, "test.txt")

        assert buffer.getvalue() == test_content
        assert buffer.tell() == 0
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key=path
        )


@pytest.mark.asyncio
async def test_badgerdoc_download_perm_clears_buffer():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    path = "data/workflows/test_workflow/TestWorkflow/workflow-123/test.txt"
    test_content = b"New content"
    buffer = BytesIO(b"Old content")

    with patch("badgerdoc_common.storage._get_s3_client") as mock_get_client:
        mock_s3_client = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_get_client.return_value.__aexit__.return_value = None

        async def mock_chunks():
            yield test_content

        mock_body = mock_chunks()
        mock_response = {"Body": mock_body}
        mock_s3_client.get_object = AsyncMock(return_value=mock_response)

        await badgerdoc_download_perm(buffer, params, path)

        assert buffer.getvalue() == test_content


@pytest.mark.asyncio
async def test_badgerdoc_download_perm_missing_bucket():
    params = StorageWorkflowParams(
        workflow_package="test_workflow",
        workflow_name="TestWorkflow",
        workflow_id="workflow-123",
    )
    path = "data/workflows/test_workflow/TestWorkflow/workflow-123/test.txt"
    buffer = BytesIO()

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("BADGERDOC_OBJECT_STORAGE_BUCKET", None)
        with pytest.raises(ValueError, match="Bucket name is required"):
            await badgerdoc_download_perm(buffer, params, path)
