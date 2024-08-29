from typing import List, Tuple
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError

from annotation.microservice_communication.jobs_communication import (
    JobUpdateException,
    append_job_categories,
    update_job_status,
)


@pytest.fixture
def setup_append_job_categories():
    job_id = "123"
    categories = ["Engineering", "Management"]
    tenant = "example_tenant"
    token = "example_token"
    mock_response = AsyncMock()
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    yield (job_id, categories, tenant, token, mock_response)


async def test_append_job_categories_success(
    setup_append_job_categories: Tuple[str, List[str], str, str, AsyncMock]
):
    (
        job_id,
        categories,
        tenant,
        token,
        mock_response,
    ) = setup_append_job_categories
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="")
    with patch(
        "annotation.microservice_communication.jobs_communication."
        "ClientSession.put",
        return_value=mock_response,
    ):
        await append_job_categories(job_id, categories, tenant, token)


async def test_append_job_categories_failure_non_200(
    setup_append_job_categories: Tuple[str, List[str], str, str, AsyncMock],
):
    (
        job_id,
        categories,
        tenant,
        token,
        mock_response,
    ) = setup_append_job_categories
    mock_response.status = 400
    mock_response.text = AsyncMock(
        return_value="Error updating job categories"
    )
    with patch(
        "annotation.microservice_communication.jobs_communication."
        "ClientSession.put",
        return_value=mock_response,
    ):
        with pytest.raises(JobUpdateException):
            await append_job_categories(job_id, categories, tenant, token)


async def test_append_job_categories_client_error(
    setup_append_job_categories: Tuple[str, List[str], str, str, AsyncMock]
):
    job_id, categories, tenant, token, _ = setup_append_job_categories
    with patch(
        "annotation.microservice_communication.jobs_communication."
        "ClientSession.put",
        side_effect=ClientError("Connection error"),
    ):
        with pytest.raises(JobUpdateException):
            await append_job_categories(job_id, categories, tenant, token)


@pytest.fixture
def job_status_setup():
    callback_url = "http://example.com/api/jobs"
    status = "completed"
    tenant = "example_tenant"
    token = "example_token"
    mock_response = AsyncMock()
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    yield (callback_url, status, tenant, token, mock_response)


async def test_update_job_status_success(
    job_status_setup: Tuple[str, str, str, str, AsyncMock]
):
    callback_url, status, tenant, token, mock_response = job_status_setup
    mock_response.status = 200
    with patch(
        "annotation.microservice_communication.jobs_communication."
        "ClientSession.put",
        return_value=mock_response,
    ):
        await update_job_status(callback_url, status, tenant, token)


async def test_update_job_status_failure_non_200(
    job_status_setup: Tuple[str, str, str, str, AsyncMock]
):
    callback_url, status, tenant, token, mock_response = job_status_setup
    mock_response.status = 404
    mock_response.text = AsyncMock(return_value="Not Found")
    with patch(
        "annotation.microservice_communication.jobs_communication."
        "ClientSession.put",
        return_value=mock_response,
    ):
        with pytest.raises(JobUpdateException):
            await update_job_status(callback_url, status, tenant, token)


async def test_update_job_status_client_error(
    job_status_setup: Tuple[str, str, str, str, AsyncMock]
):
    callback_url, status, tenant, token, _ = job_status_setup
    with patch(
        "annotation.microservice_communication.jobs_communication."
        "ClientSession.put",
        side_effect=ClientError("Connection Failed"),
    ):
        with pytest.raises(JobUpdateException):
            await update_job_status(callback_url, status, tenant, token)
