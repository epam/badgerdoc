from .conftest import User, Address
from src.query_modificator import (
    _get_entity,
    _get_column,
    _create_filter,
    form_query,
)


def test_get_entity(get_session):
    session = get_session
    query = session.query(User, Address)
    assert _get_entity(query, "User") == User
    assert _get_entity(query, "Address") == Address


def test_get_column_positive():
    assert _get_column(User, "id") == User.id
    assert _get_column(User, "name") == User.name
    assert _get_column(Address, "location") == Address.location


def test_create_filter(get_session):
    session = get_session
    user_1 = User(name="test_one")
    user_2 = User(name="test_two")
    session.add_all([user_1, user_2])
    session.commit()

    query = session.query(User)
    spec = {"model": "User", "field": "name", "op": "eq", "value": "test_one"}
    query = _create_filter(query, spec)
    assert len(query.all()) == 1


def test_form_query(get_session):
    session = get_session
    user_1 = User(id=5, name="user")
    user_2 = User(id=10, name="user")
    user_3 = User(id=15)
    user_4 = User(id=20)
    session.add_all([user_1, user_2, user_3, user_4])
    session.commit()

    query = session.query(User)
    specs = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [
            {"model": "User", "field": "id", "op": "le", "value": 20},
            {"model": "User", "field": "name", "op": "like", "value": "user"},
        ],
    }
    query, pag = form_query(specs, query)
    assert len(query.all()) == 2
    assert (pag.page_num, pag.page_size, pag.min_pages_left, pag.total) == (
        1,
        15,
        1,
        2,
    )
