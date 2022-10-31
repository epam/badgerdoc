from .conftest import User, Address
from ..src.schema_generator import (
    create_filter_model,
    Page,
    PaginationOut,
)


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
        page_num=1, page_size=15, min_pages_left=1, total=3, has_more=False
    )
    page = Page(pagination=test_pag, data=test_resp)
    assert page == {
        "pagination": {
            "min_pages_left": 1,
            "page_num": 1,
            "page_size": 15,
            "total": 3,
            "has_more": False,
        },
        "data": test_resp,
    }
