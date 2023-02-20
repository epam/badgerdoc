import pytest
from pydantic import ValidationError

from ..src.pagination import (PaginationParams, _calculate_num_pages,
                              make_pagination, paginate)
from .conftest import User


@pytest.mark.parametrize(
    "page_num, page_size, min_pages_left, total, has_more",
    [
        (1, 1, 1, 1, True),
        (0, 0, 0, 0, False),
        (10, 10, 10, 10, False),
    ],
)
def test_pag_params(page_num, page_size, min_pages_left, total, has_more):
    res = PaginationParams(
        page_num, page_size, min_pages_left, total, has_more
    )
    assert (
        res.page_num,
        res.page_size,
        res.min_pages_left,
        res.total,
        res.has_more,
    ) == (page_num, page_size, min_pages_left, total, has_more)


@pytest.mark.parametrize(
    ("sequence", "pag_params"),
    [
        ([1, 2, 3], [1, 15, 1, 1, False]),
        (["one", "two", "three"], [1, 100, 1, 3, False]),
        ([], [1, 15, 0, 0, False]),
        ((), [1, 15, 0, 0, False]),
    ],
)
def test_paginate_positive(sequence, pag_params):
    pag = PaginationParams(*pag_params)
    assert paginate(sequence, pag) == {
        "pagination": {
            "page_num": pag.page_num,
            "page_size": pag.page_size,
            "min_pages_left": pag.min_pages_left,
            "total": pag.total,
            "has_more": pag.has_more,
        },
        "data": sequence,
    }


@pytest.mark.parametrize(
    "start, stop, expected_result",
    [
        (1, 150, (1, 15, 10, 149, False)),
        (1, 151, (1, 15, 10, 150, False)),
        (1, 152, (1, 15, 10, 150, True)),
    ],
)
def test_make_pagination_max_count(get_session, start, stop, expected_result):
    session = get_session
    new_users = [User(id=i, name=f"user{i}") for i in range(start, stop)]
    session.add_all(new_users)
    session.commit()

    page_num, page_size = 1, 15
    users = session.query(User)
    query, pag = make_pagination(users, page_num, page_size)
    assert len(query.all()) == page_size
    assert (
        pag.page_num,
        pag.page_size,
        pag.min_pages_left,
        pag.total,
        pag.has_more,
    ) == expected_result


def test_paginate_negative_validation_error():
    pag = PaginationParams(1, 10, 0, 0, False)
    with pytest.raises(ValidationError):
        paginate((1, 2, 3), pag)


def test_make_pagination(get_session):
    session = get_session
    new_users = [User(id=i, name=f"user{i}") for i in range(1, 21)]
    session.add_all(new_users)
    session.commit()

    page_num, page_size = 1, 15
    users = session.query(User)
    query, pag = make_pagination(users, page_num, page_size)
    assert len(query.all()) == page_size
    assert (
        pag.page_num,
        pag.page_size,
        pag.min_pages_left,
        pag.total,
        pag.has_more,
    ) == (1, 15, 2, 20, False)


def test_calculate_num_pages():
    assert _calculate_num_pages(15, 29) == 2
    assert _calculate_num_pages(100, 101) == 2
    assert _calculate_num_pages(15, 14) == 1
    assert _calculate_num_pages(15, 0) == 0
