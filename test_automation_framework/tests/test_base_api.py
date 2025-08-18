from logging import getLogger
import pytest
from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


class TestAuthAPI:
    def test_basic_auth(self, auth_token):
        access_token, refresh_token = auth_token
        assert access_token, "No access_token found!"
        assert refresh_token, "No refresh_token found!"

    def test_wrong_creds(self, auth_service):
        with pytest.raises(HTTPError) as e:
            auth_service.get_token("wrong", "wrong")
        assert (
            e.value.status_code == 401
        ), f"Expected 401 but got {e.value.status_code}: {e.value.body}"

    def test_refresh_token(self, auth_token, auth_service):
        access_token, refresh_token = auth_token
        new_access_token, new_refresh_token = auth_service.refresh_token(
            refresh_token=refresh_token
        )
        assert (
            new_access_token != access_token
        ), "Old access token is the same as new access token!"
        assert (
            new_refresh_token != refresh_token
        ), "Old refresh token is the same as new refresh token!"
