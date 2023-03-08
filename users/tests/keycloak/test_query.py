"""Testing src/keycloak/query.py."""
from unittest.mock import patch

import pytest
import users.keycloak.query as query
import users.keycloak.schemas as schemas


@pytest.fixture
def request_mock():
    with patch("users.keycloak.query.aiohttp.request") as mock:
        yield mock


def test_create_bearer_header():
    """Testing create_bearer_header."""
    assert query.create_bearer_header("foo") == {"Authorization": "Bearer foo"}


@pytest.mark.asyncio
async def test_get_token_v2(request_mock):
    """Testing get_token."""
    token = {"access_token": "foo", "token_type": "Bearer"}
    token_req = schemas.TokenRequest(
        username="john", password="123", client_id="client"
    )
    request_mock.return_value.__aenter__.return_value.json.return_value = token
    resp = await query.get_token_v2("master", token_req)
    assert resp == schemas.TokenResponse.parse_obj(token)


@pytest.mark.asyncio
async def test_introspect_token_test(
    request_mock, mocked_token1, mocked_token1_data
):
    request_mock.return_value.__aenter__.return_value.json.return_value = (
        mocked_token1_data
    )
    result = await query.introspect_token(mocked_token1)
    assert result == mocked_token1_data


@pytest.mark.asyncio
async def test_get_master_realm_auth_data(
    request_mock, mocked_admin_auth_data
):
    request_mock.return_value.__aenter__.return_value.json.return_value = (
        mocked_admin_auth_data
    )
    result = await query.get_master_realm_auth_data()
    assert result == mocked_admin_auth_data


@pytest.mark.asyncio
async def test_get_identity_providers_data(
    request_mock, mocked_identity_providers_data
):
    request_mock.return_value.__aenter__.return_value.json.return_value = (
        mocked_identity_providers_data
    )
    mock_access_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJIY0dZYXVPeV9rN0tQLUpDdlJNUjd5b3BnV2pEc2lob2k0NW8zZElNQ0o0In0.eyJleHAiOjE2NDMzODQyMTIsImlhdCI6MTY0MzAyNDIxMiwianRpIjoiMWY4MWQzZjItNjZiMC00M2UyLTlhYjEtZTljZmUzYjNmNjgxIiwiaXNzIjoiaHR0cDovL2RldjIuZ2Nvdi5ydS9hdXRoL3JlYWxtcy9tYXN0ZXIiLCJzdWIiOiIwMjMzNjY0Ni1mNWQwLTQ2NzAtYjExMS1jMTQwYTNhZDU4YjUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhZG1pbi1jbGkiLCJzZXNzaW9uX3N0YXRlIjoiNzMyZmE1OTItN2EzNy00OTUwLThmM2UtZjIzYzQwODVkMTA0IiwiYWNyIjoiMSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJjcmVhdGUtcmVhbG0iLCJyb2xlLWFubm90YXRvciIsImFkbWluIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsibWFzdGVyLXJlYWxtIjp7InJvbGVzIjpbInZpZXctcmVhbG0iLCJ2aWV3LWlkZW50aXR5LXByb3ZpZGVycyIsIm1hbmFnZS1pZGVudGl0eS1wcm92aWRlcnMiLCJpbXBlcnNvbmF0aW9uIiwiY3JlYXRlLWNsaWVudCIsIm1hbmFnZS11c2VycyIsInF1ZXJ5LXJlYWxtcyIsInZpZXctYXV0aG9yaXphdGlvbiIsInF1ZXJ5LWNsaWVudHMiLCJxdWVyeS11c2VycyIsIm1hbmFnZS1ldmVudHMiLCJtYW5hZ2UtcmVhbG0iLCJ2aWV3LWV2ZW50cyIsInZpZXctdXNlcnMiLCJ2aWV3LWNsaWVudHMiLCJtYW5hZ2UtYXV0aG9yaXphdGlvbiIsIm1hbmFnZS1jbGllbnRzIiwicXVlcnktZ3JvdXBzIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwic2lkIjoiNzMyZmE1OTItN2EzNy00OTUwLThmM2UtZjIzYzQwODVkMTA0IiwidGVuYW50cyI6WyJ0ZXN0Il0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWRtaW4ifQ.Pqjodk9-QPmLxAagcs1_LP_zLzJ_77a2FTjL7kQn7GB-Tu2kZbZMMRuwzmlRj3dYKJFBsEiE5vykmTVrBqRAFpUC9cpQ2LWe8xKagwJmW8CIB53nSUhE1hx8_YSn1vzR0lu1S8j1PtzcnJVvPL8YMPPjCt6TFNgJkQo_jgwuhHXexFKy1JyQKb-nrN5jF-MvQvWhHro-33bDQTckBAdIaedAzfm-ZqlFL4Ohw9yW8ANzMYXHrfkIf3AALwv07D2SWn9ht0xSxAytOSXyvsnHzi9FIYp0uIAo-0dP02ULIpQYlFapw179H6KwlXmbW08BYVLQzpga6U7a39KQ07SS-A"  # noqa
    result = await query.get_identity_providers_data(mock_access_token)
    assert result == mocked_identity_providers_data
