import pytest
from pydantic import ValidationError
from src.schema_generator import (
    Page,
    Pagination,
    PaginationOut,
    create_filter_model,
)
from tests.conftest import Address, User


def test_search_class_creating():
    UserFilter = create_filter_model(User)
    assert UserFilter.schema()["definitions"]["users_User"]["enum"] == [
        "id",
        "name",
        "email",
        "addresses.id",
        "addresses.location",
        "addresses.owner",
    ]

    AddressFilter = create_filter_model(Address, exclude=["location"])
    assert AddressFilter.schema()["definitions"]["addresses_Address"][
        "enum"
    ] == ["id", "owner", "user.id", "user.name", "user.email"]


def test_page_schema():
    test_resp = [1, 2, 3]
    test_pag = PaginationOut(
        page_num=1,
        page_size=15,
        min_pages_left=1,
        total=3,
        has_more=False,
        page_offset=0,
    )
    page = Page(pagination=test_pag, data=test_resp)
    assert page == {
        "pagination": {
            "min_pages_left": 1,
            "page_num": 1,
            "page_size": 15,
            "total": 3,
            "has_more": False,
            "page_offset": 0,
        },
        "data": test_resp,
    }


def test_pagination_schema_validation_with_page_num_and_page_size_positive_case():
    pagination_data = {"page_num": 1, "page_size": 15}
    Pagination(**pagination_data)


def test_pagination_schema_validation_with_page_offset_and_page_size_positive_case():
    pagination_data = {"page_offset": 0, "page_size": 15}
    Pagination(**pagination_data)


def test_pagination_schema_validation_incorrect_page_num():
    pagination_data = {"page_num": 0, "page_size": 15}
    with pytest.raises(ValidationError):
        Pagination(**pagination_data)


def test_pagination_schema_validation_page_num_and_page_offset_sent():
    pagination_data = {"page_num": 1, "page_size": 15, "page_offset": 10}
    with pytest.raises(
        ValidationError,
        match=r"'page_num' and 'page_offset' cannot be used together",
    ):
        Pagination(**pagination_data)


def test_pagination_schema_validation_page_num_and_page_offset_not_sent():
    pagination_data = {
        "page_size": 15,
    }
    with pytest.raises(
        ValidationError,
        match=r"'page_num' or 'page_offset' are missing. "
        "One of these attributes shoud be used",
    ):
        Pagination(**pagination_data)
