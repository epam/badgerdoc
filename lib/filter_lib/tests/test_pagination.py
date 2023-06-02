import pytest
from pydantic import ValidationError

from src.pagination import (
    PaginationParams,
    _calculate_num_pages,
    make_pagination,
    paginate,
)
from src.query_modificator import form_query
from src.schema_generator import Page, PaginationOut
from tests.conftest import User


@pytest.mark.parametrize(
    "page_num, page_size, min_pages_left, total, has_more, page_offset",
    [
        (1, 1, 1, 1, True, None),
        (0, 0, 0, 0, False, None),
        (10, 10, 10, 10, False, None),
    ],
)
def test_pag_params(
    page_num, page_size, min_pages_left, total, has_more, page_offset
):
    res = PaginationParams(
        page_num, page_size, min_pages_left, total, has_more, page_offset
    )
    assert (
        res.page_num,
        res.page_size,
        res.min_pages_left,
        res.total,
        res.has_more,
        res.page_offset,
    ) == (page_num, page_size, min_pages_left, total, has_more, page_offset)


@pytest.mark.parametrize(
    ("sequence", "pag_params"),
    [
        ([1, 2, 3], [1, 15, 1, 1, False, 0]),
        (["one", "two", "three"], [1, 100, 1, 3, False, 0]),
        ([], [1, 15, 0, 0, False, 0]),
        ((), [1, 15, 0, 0, False, 0]),
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
            "page_offset": 0,
        },
        "data": sequence,
    }


@pytest.mark.parametrize(
    "start, stop, page_num, page_size, page_offset, found_items, expected_result",
    [
        (1, 150, 1, 15, None, 15, (1, 15, 10, 149, False, 0)),
        (1, 151, 1, 15, None, 15, (1, 15, 10, 150, False, 0)),
        (1, 152, 1, 15, None, 15, (1, 15, 10, 150, True, 0)),
        (1, 150, 11, 15, None, 0, (11, 15, 0, 0, False, 150)),
        (1, 151, 5, 10, None, 10, (5, 10, 10, 100, True, 40)),
        (1, 151, 6, 10, None, 10, (6, 10, 10, 100, False, 50)),
        (1, 151, 7, 10, None, 10, (7, 10, 9, 90, False, 60)),
    ],
)
def test_make_pagination_max_count(
    get_session,
    start,
    stop,
    page_num,
    page_size,
    page_offset,
    found_items,
    expected_result,
):
    session = get_session
    new_users = [User(id=i, name=f"user{i}") for i in range(start, stop)]
    session.add_all(new_users)
    session.commit()

    if page_offset is not None:
        offset = page_offset
        max_count = page_size + 1
    elif page_num is not None:
        offset = (page_num - 1) * page_size
        max_count = page_size * 10 + 1

    users = session.query(User)
    query, pag = make_pagination(
        initial_query=users,
        page_num=page_num,
        page_size=page_size,
        page_offset=offset,
        max_count=max_count,
    )
    assert len(query.all()) == found_items
    assert (
        pag.page_num,
        pag.page_size,
        pag.min_pages_left,
        pag.total,
        pag.has_more,
        pag.page_offset,
    ) == expected_result


def test_paginate_negative_validation_error():
    pag = PaginationParams(1, 10, 0, 0, False, None)
    with pytest.raises(ValidationError):
        paginate((1, 2, 3), pag)


def test_make_pagination(get_session):
    session = get_session
    new_users = [User(id=i, name=f"user{i}") for i in range(1, 21)]
    session.add_all(new_users)
    session.commit()

    page_num, page_size, page_offset = 1, 15, None
    if page_offset is not None:
        offset = page_offset
        max_count = page_size + 1
    elif page_num is not None:
        offset = (page_num - 1) * page_size
        max_count = page_size * 10 + 1

    users = session.query(User)
    query, pag = make_pagination(
        initial_query=users,
        page_num=page_num,
        page_size=page_size,
        page_offset=offset,
        max_count=max_count,
    )
    assert len(query.all()) == page_size
    assert (
        pag.page_num,
        pag.page_size,
        pag.min_pages_left,
        pag.total,
        pag.has_more,
        pag.page_offset,
    ) == (1, 15, 2, 20, False, 0)


def test_calculate_num_pages():
    assert _calculate_num_pages(15, 29) == 2
    assert _calculate_num_pages(100, 101) == 2
    assert _calculate_num_pages(15, 14) == 1
    assert _calculate_num_pages(15, 0) == 0


@pytest.mark.parametrize(
    "page_offset_and_page_size",
    [(0, 15), (0, 100), (10, 30), (50, 80), (50, 100), (80, 30)],
)
def test_paginate_uii_compatible_format(
    get_session, page_offset_and_page_size
):
    session = get_session
    user_instances_to_create = [User(id=idx) for idx in range(1, 101)]
    session.add_all(user_instances_to_create)
    session.commit()
    query = session.query(User)

    page_offset, page_size = page_offset_and_page_size

    specs = {
        "pagination": {"page_offset": page_offset, "page_size": page_size}
    }
    query, pag = form_query(specs, query)

    start_slice_num = page_offset
    stop_slice_num = page_offset + page_size

    if page_offset + page_size > len(user_instances_to_create):
        expected_total = len(user_instances_to_create) - page_offset
    else:
        expected_total = page_size

    paginated_data = paginate(query.all(), pag)

    assert paginated_data == Page(
        pagination=PaginationOut(
            page_num=None,
            page_offset=page_offset,
            page_size=page_size,
            total=expected_total,
            has_more=(
                query.count()
                < len(
                    user_instances_to_create[
                        start_slice_num : stop_slice_num + 1
                    ]
                )
            ),
            min_pages_left=1,
        ),
        data=query.all(),
    )
