import users.keycloak.utils as kc_utils
from users.schemas import Users
import pytest


@pytest.fixture
def request_body():
    return [
        {"field": "name", "operator": "like", "value": "h"},
        {"field": "id", "operator": "in", "value": ["user_id"]},
        {"field": "role", "operator": "eq", "value": "role-annotator"},
    ]


@pytest.mark.parametrize(
    "request_body",
    [
        None,
        [],
    ],
)
def test_create_filters_with_empty_request_body(request_body):
    users = Users(filters=request_body)
    filters = kc_utils.create_filters(users)
    assert filters == {}


def test_create_filters(request_body):
    users = Users(filters=request_body)
    filters = kc_utils.create_filters(users)
    assert filters == {
        "name": "h",
        "id": ["user_id"],
        "role": "role-annotator",
    }
