from unittest.mock import Mock, patch

import pytest

import veeva.services.veeva_synchronization
from veeva.models.orm import Synchronization
from veeva.services import veeva_synchronization


@pytest.fixture
def mock_configuration():
    config = Mock()
    config.veeva_pm_host = "test_host.com"
    config.veeva_pm_login = "test_login"
    config.veeva_pm_password = "test_password"
    config.veeva_pm_vql = "test_vql"
    return config


@pytest.fixture
def mock_synchronization(mock_configuration):
    sync = Mock(spec=Synchronization)
    sync.configuration = mock_configuration
    # Create a custom __str__ method as a mock function
    str_mock = Mock(return_value="Test Synchronization")
    sync.__str__ = str_mock
    return sync


@pytest.mark.asyncio
async def test_run(
    mock_session,
    mock_synchronization,
):
    with patch(
        "veeva.services.veeva_synchronization.logger.info"
    ) as mock_logger:
        await veeva.services.veeva_synchronization.run(
            session=mock_session,
            synchronization=mock_synchronization,
        )
        mock_logger.assert_any_call(
            "Running synchronization job: %s", mock_synchronization
        )


@pytest.mark.asyncio
async def test_run_logs_configuration_details(
    mock_session,
    mock_synchronization,
):
    with patch(
        "veeva.services.veeva_synchronization.logger.info"
    ) as mock_logger:
        await veeva.services.veeva_synchronization.run(
            session=mock_session,
            synchronization=mock_synchronization,
        )

        mock_logger.assert_any_call(
            "Configuration: %s", mock_synchronization.configuration
        )
        mock_logger.assert_any_call(
            "Veeva PM host: %s",
            mock_synchronization.configuration.veeva_pm_host,
        )
        mock_logger.assert_any_call(
            "Veeva PM login: %s",
            mock_synchronization.configuration.veeva_pm_login,
        )
        mock_logger.assert_any_call(
            "Veeva PM password: %s",
            mock_synchronization.configuration.veeva_pm_password,
        )
        mock_logger.assert_any_call(
            "Veeva PM VQL: %s", mock_synchronization.configuration.veeva_pm_vql
        )


@pytest.mark.asyncio
async def test_run_with_exception(
    mock_session,
    mock_synchronization,
):
    with patch(
        "veeva.services.veeva_synchronization.logger.info"
    ) as mock_logger:
        mock_logger.side_effect = Exception("Test exception")

        with pytest.raises(Exception) as excinfo:
            await veeva.services.veeva_synchronization.run(
                session=mock_session,
                synchronization=mock_synchronization,
            )

        assert "Test exception" in str(excinfo.value)


@pytest.mark.asyncio
@pytest.mark.skip("Skipping test_auth_success due to external dependencies")
async def test_auth_success(mock_synchronization):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json = Mock(return_value={"sessionId": "test-session-id"})

    mock_session = Mock()
    mock_session.post = Mock(return_value=mock_response)

    with patch(
        "veeva.services.veeva_synchronization.logger.info"
    ) as mock_logger:
        result = await veeva.services.veeva_synchronization.auth(
            mock_synchronization
        )

    pass


def test_map_response_to_session():
    mapped_sync = veeva.services.veeva_synchronization.map_response_to_session(
        {
            "responseStatus": "SUCCESS",
            "sessionId": "TEST_SESSION_ID",
            "userId": 1,
            "vaultIds": [
                {
                    "id": 2,
                    "name": "Test PromoMats",
                    "url": "https://example.com/api",
                }
            ],
            "vaultId": 2,
        }
    )
    assert (
        veeva_synchronization.VeevaPmSession(
            session_id="TEST_SESSION_ID",
            response_status="SUCCESS",
            user_id=1,
            vault_id=2,
            vault_ids=[
                veeva_synchronization.VeevaPmVault(
                    id=2, name="Test PromoMats", url="https://example.com/api"
                )
            ],
        )
        == mapped_sync
    )
