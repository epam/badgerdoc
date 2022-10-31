import src.keycloak.utils as kc_utils
import src.keycloak.schemas as kc_schemas
import pytest

user_1 = kc_schemas.User(username="user", id="1")
user_2 = kc_schemas.User(username="u__r", id="2")
mock_users = [user_1, user_2]


@pytest.mark.parametrize(
    ("filters", "expected_result"),
    [
        ({}, [user_1, user_2]),
        ({"user_name_substring": "u"}, [user_1, user_2]),
        ({"user_name_substring": "_"}, [user_2]),
        ({"user_name_substring": "U"}, []),
        ({"user_id": ["1"]}, [user_1]),
        ({"user_id": ["3"]}, []),
        ({"user_id": ["2", "3"]}, [user_2]),
        ({"user_id": ["1", "2"]}, [user_1, user_2]),
        ({"user_id": []}, []),
        ({"user_name_substring": "user", "user_id": ["2"]}, []),
        ({"user_name_substring": "user", "user_id": ["1", "2"]}, [user_1]),
    ],
)
def test_user(filters, expected_result):
    users_list = kc_schemas.User.filter_users(users=mock_users, **filters)
    assert users_list == expected_result
