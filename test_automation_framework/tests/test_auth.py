from logging import getLogger

import pytest


from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


class TestAuthAPI:
    def test_basic_auth(self, auth_token):
        access_token, refresh_token = auth_token
        assert access_token
        assert refresh_token

    def test_wrong_creds(self, auth_service):
        with pytest.raises(HTTPError) as exc:
            auth_service.get_token("wrong", "wrong")
        assert exc.value.status_code == 401

    def test_refresh_token(self, auth_token, auth_service):
        access_token, refresh_token = auth_token
        new_access, new_refresh = auth_service.refresh_token(refresh_token=refresh_token)
        assert new_access != access_token
        assert new_refresh != refresh_token
