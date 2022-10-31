from src.schemas import Users


def test_users_schemas():
    users = Users(
        filters=[
            {"field": "name", "operator": "like", "value": "h"},
            {"field": "role", "operator": "eq", "value": "role-annotator"},
        ]
    )

    assert users.filters == [
        {"field": "name", "operator": "like", "value": "h"},
        {"field": "role", "operator": "eq", "value": "role-annotator"},
    ]
