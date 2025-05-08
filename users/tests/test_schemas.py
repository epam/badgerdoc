from users.schemas import Users


def test_users_schemas():
    users = Users(
        filters=[
            {"field": "name", "operator": "like", "value": "h"},
            {"field": "role", "operator": "eq", "value": "role-annotator"},
        ]
    )

    result_to_check = [f.model_dump(mode="json") for f in users.filters]

    assert result_to_check == [
        {"field": "name", "operator": "like", "value": "h"},
        {"field": "role", "operator": "eq", "value": "role-annotator"},
    ]
