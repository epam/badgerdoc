import uuid
from json import loads
from typing import Any, List, Optional, Tuple, Union
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import fixture, mark
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models import Category
from tests.consts import CATEGORIES_PATH
from tests.override_app_dependency import TEST_HEADERS, app

client = TestClient(app)

ATTRIBUTES_NOT_IN_CATEGORY_MODEL = ("is_leaf",)
NOT_FULLY_TEST_SUPPORTED_CATEGORY_ATTRIBUTES = (
    "parents",
    "is_leaf",
    "id",
)


def clean_data_for_db(data):
    cleaned_data = {
        key: value
        for key, value in data.items()
        if key not in ATTRIBUTES_NOT_IN_CATEGORY_MODEL
    }
    return cleaned_data


def prepare_category_body(
    id_: Optional[str] = None,
    name: Optional[str] = "Title1",
    parent: Optional[str] = None,
    metadata: Optional[dict] = None,
    type: Optional[str] = "box",
    body_other_tenant: Optional[bool] = False,
    editor: Optional[str] = None,
    data_attributes: Optional[List[dict]] = None,
    is_leaf=True,
) -> dict:
    body = {
        "data_attributes": data_attributes,
        "editor": editor,
        "id": id_,
        "type": type,
        "metadata": metadata,
        "name": name,
        "parent": parent,
        "is_leaf": is_leaf,
    }
    if body_other_tenant:
        body["tenant"] = "other_tenant"
    return {key: body[key] for key in sorted(body)}


def prepare_filtration_body(
    page_num: Optional[int] = 1,
    page_size: Optional[int] = 15,
    field: Optional[str] = "id",
    operator: Optional[str] = "eq",
    value: Optional[Any] = 1,
    direction: Optional[str] = "asc",
    no_filtration: Optional[bool] = False,
) -> dict:
    body = {
        "pagination": {
            "page_num": page_num,
            "page_size": page_size,
        },
        "filters": [
            {
                "field": field,
                "operator": operator,
                "value": value,
            }
        ],
        "sorting": [
            {
                "field": "id",
                "direction": direction,
            }
        ],
    }
    if no_filtration:
        body.pop("filters")
    return body


def prepare_filtration_body_double_filter(
    page_num: Optional[int] = 1,
    page_size: Optional[int] = 15,
    first_field: Optional[str] = "editor",
    second_field: Optional[str] = "type",
    sorting_field: Optional[str] = "type",
    first_operator: Optional[str] = "distinct",
    second_operator: Optional[str] = "distinct",
    value: Optional[Any] = "string",
    direction: Optional[str] = "asc",
    no_filtration: Optional[bool] = False,
) -> dict:
    body = {
        "pagination": {
            "page_num": page_num,
            "page_size": page_size,
        },
        "filters": [
            {
                "field": first_field,
                "operator": first_operator,
                "value": value,
            },
            {
                "field": second_field,
                "operator": second_operator,
                "value": value,
            },
        ],
        "sorting": [
            {
                "field": sorting_field,
                "direction": direction,
            }
        ],
    }
    if no_filtration:
        body.pop("filters")
    return body


def prepare_expected_result(
    response: Union[str, dict], with_category_id: bool = False
) -> dict:
    response_map = loads(response) if isinstance(response, str) else response
    if not with_category_id:
        response_map["id"] = None
    return {
        key: response_map[key]
        for key in sorted(response_map)
        if key not in NOT_FULLY_TEST_SUPPORTED_CATEGORY_ATTRIBUTES
    }


def prepare_category_response(data: dict) -> dict:
    data = {
        key: value
        for key, value in data.items()
        if key not in NOT_FULLY_TEST_SUPPORTED_CATEGORY_ATTRIBUTES
    }
    return data


@fixture
def add_for_cascade_delete(
    prepare_db_categories_different_names, request
) -> Tuple[int, int]:
    parent_id = request.param
    session = prepare_db_categories_different_names
    data_1 = prepare_category_body(name="Title1", parent=parent_id)
    response_1 = client.post(
        CATEGORIES_PATH, json=data_1, headers=TEST_HEADERS
    )
    cat_id_1 = response_1.json()["id"]
    data_2 = prepare_category_body(name="Title3", parent=cat_id_1)
    response_2 = client.post(
        CATEGORIES_PATH, json=data_2, headers=TEST_HEADERS
    )
    cat_id_2 = response_2.json()["id"]
    common_cat = session.query(Category).get("2")
    session.delete(common_cat)
    session.commit()
    yield cat_id_1, cat_id_2


@mark.integration
@patch("app.categories.resources.add_category_db", side_effect=SQLAlchemyError)
def test_add_db_connection_error(prepare_db_categories_different_names):
    data = prepare_category_body()
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@mark.integration
@mark.parametrize(
    ["category_id", "category_name"],
    [  # this tenant and common category already exist names
        (None, "Title"),
        ("my_favourite_category", "Table"),  # unique id
    ],
)
def test_add_already_exist_category_name(
    prepare_db_categories_different_names, category_id, category_name
):
    data = prepare_category_body(id_=category_id, name=category_name)
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 400
    assert "Category name must be unique" in response.text


@mark.integration
@mark.parametrize(
    "category_name",
    ("Title1", "Header"),  # new unique name and other tenant category name
)
def test_add_unique_name(prepare_db_categories_different_names, category_name):
    data = prepare_category_body(name=category_name)
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 201
    assert prepare_expected_result(response.text) == prepare_category_response(
        data
    )


@mark.integration
@mark.parametrize(
    "field_value_pairs",
    [
        {"metadata": {"color": "red", "size": 100}},
        {"metadata": {"color": "blue"}},  # custom values in metadata field
        {"type": "link"},  # custom values in type field
        {"parent": "1"},  # custom value parent field, parent from this tenant
        {"parent": "2"},  # custom value parent field, parent from commons
        {"editor": "http://editor/"},  # custom value in editor field
        {"data_attributes": [{"attr 1": 123}]},  # custom data_attributes
    ],
)
def test_add_unique_name_custom_fields(
    prepare_db_categories_different_names, field_value_pairs
):
    data = prepare_category_body(**field_value_pairs)
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 201
    assert prepare_expected_result(response.text) == prepare_category_response(
        data
    )


@mark.integration
@mark.parametrize(
    ["wrong_field", "wrong_value"],
    [
        ("metadata", "string"),
        ("type", 100),
        ("parent", ("1", "2")),
        ("editor", ("1", "2")),
        ("data_attributes", "string"),
    ],
)
def test_add_wrong_field_types(db_session, wrong_field, wrong_value):
    wrong_body = {
        "name": "Name",
        "parent": None,
        "metadata": None,
        "type": "box",
        "editor_url": None,
        "data_attributes": None,
        wrong_field: wrong_value,  # rewrite default value with parametrized
    }
    response = client.post(
        CATEGORIES_PATH, json=wrong_body, headers=TEST_HEADERS
    )
    assert response.status_code == 422


@mark.integration
@mark.parametrize(
    ["category_parent", "expected_message"],
    [
        ("3", "Foreign key error"),  # parent category from other tenant
        ("100", "Key (parent)=(100) is not present in table"),  # doesn't exist
    ],
)
def test_add_wrong_parent(
    category_parent,
    expected_message,
    prepare_db_categories_different_names,
):
    data = prepare_category_body(parent=category_parent)
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 500
    assert expected_message in response.text


@mark.integration
def test_add_without_name(prepare_db_categories_different_names):
    data = prepare_category_body(name=None)
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 422
    assert "none is not an allowed value" in response.text


@mark.integration
def test_add_other_tenant_body_parent(prepare_db_categories_different_names):
    data = prepare_category_body(parent="3", body_other_tenant=True)
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 500
    assert "Foreign key error" in response.text


@mark.integration
def test_add_id_already_exists(prepare_db_categories_different_names):
    data = prepare_category_body(id_="1")
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 400
    assert "Category id must be unique" in response.text


@mark.integration
def test_add_id_is_unique(prepare_db_categories_different_names):
    data = prepare_category_body(id_="my_favourite_category")
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 201
    assert prepare_expected_result(
        response.text, with_category_id=True
    ) == prepare_category_response(data)


@mark.integration
@patch("uuid.uuid4", return_value=UUID("fe857daa-8332-4a26-ab50-29be0a74477e"))
def test_add_id_is_generated(prepare_db_categories_different_names):
    data = prepare_category_body()
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    mocked_id = str(uuid.uuid4())
    data_with_mocked_id = prepare_category_body(id_=mocked_id)
    assert response.status_code == 201
    assert prepare_expected_result(
        response.text, with_category_id=True
    ) == prepare_category_response(data_with_mocked_id)


@mark.integration
@patch("app.categories.resources.link_category_with_taxonomy")
@patch("uuid.uuid4", return_value="fe857daa-8332-4a26-ab50-29be0a74477e")
def test_should_send_link_request_taxonomy_service(
    uuid_mock, link_request_mock, prepare_db_categories_different_names
):
    data = prepare_category_body(
        id_="1213",
        name="taxonomy_12",
        data_attributes=[{"taxonomy_id": "123"}, {"taxonomy_version": 1}],
    )
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response
    assert response.status_code == 201
    assert link_request_mock.called


@mark.integration
def test_add_self_parent(prepare_db_categories_different_names):
    data = prepare_category_body(id_="category", parent="category")
    response = client.post(CATEGORIES_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 400
    assert "Category cannot be its own parent." in response.text


@mark.integration
@patch(
    "app.categories.resources.fetch_category_db", side_effect=SQLAlchemyError
)
def test_get_db_connection_error(prepare_db_categories_same_names):
    cat_id = 1
    response = client.get(f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS)
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@mark.integration
@mark.parametrize(
    "category_id",
    ("3", "100"),  # other tenant category and category that doesn't exist
)
def test_get_wrong_category(category_id, prepare_db_categories_same_names):
    response = client.get(
        f"{CATEGORIES_PATH}/{category_id}", headers=TEST_HEADERS
    )
    assert response.status_code == 404
    assert f"Category with id: {category_id} doesn't exist" in response.text


@mark.integration
@mark.parametrize(
    ["category_id", "category_name"],
    [
        (1, "Title"),  # this tenant category id and name
        (2, "Table"),  # common category id and name
    ],
)
def test_get_allowed_category(
    category_id, category_name, prepare_db_categories_same_names
):
    data = prepare_category_body(name=category_name)
    response = client.get(
        f"{CATEGORIES_PATH}/{category_id}", headers=TEST_HEADERS
    )
    assert response.status_code == 200
    assert prepare_expected_result(response.text) == prepare_category_response(
        data
    )


@mark.integration
def test_get_no_tenant_specified(prepare_db_categories_same_names):
    cat_id = 1
    response = client.get(f"{CATEGORIES_PATH}/{cat_id}")
    assert response.status_code == 422
    assert "field required" in response.text


@mark.integration
@patch(
    "app.categories.resources.filter_category_db", side_effect=SQLAlchemyError
)
def test_search_db_connection_error(prepare_db_categories_for_filtration):
    data = prepare_filtration_body()
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@mark.integration
@mark.parametrize(
    ["page_num", "page_size", "result_length"],
    [(1, 15, 15), (2, 15, 1), (3, 15, 0), (1, 30, 16)],
)
def test_search_pagination(
    page_num, page_size, result_length, prepare_db_categories_for_filtration
):
    data = prepare_filtration_body(
        page_num=page_num, page_size=page_size, no_filtration=True
    )
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    categories = response.json()["data"]
    pagination = response.json()["pagination"]
    assert response.status_code == 200
    assert pagination["total"] == 16
    assert pagination["page_num"] == page_num
    assert pagination["page_size"] == page_size
    assert len(categories) == result_length


@mark.integration
def test_search_no_filtration(prepare_db_categories_for_filtration):
    data = prepare_filtration_body(page_size=30, no_filtration=True)
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    categories = response.json()["data"]
    assert response.status_code == 200
    assert len(categories) == 16


@mark.integration
@mark.parametrize(
    "category_id",
    ("2", "100"),  # other tenant category and category that doesn't exist
)
def test_search_wrong_category(
    category_id, prepare_db_categories_for_filtration
):
    data = prepare_filtration_body(value=category_id)
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    categories = response.json()["data"]
    total = response.json()["pagination"]["total"]
    assert response.status_code == 200
    assert not total
    assert not categories


@mark.integration
@mark.parametrize(
    ["category_id", "category_name"],
    [
        ("1", "Title"),  # this tenant category id and name
        ("3", "Table1"),  # common category id and name
    ],
)
def test_search_allowed_categories(
    category_id,
    category_name,
    prepare_db_categories_for_filtration,
):
    expected = prepare_category_body(name=category_name)
    data = prepare_filtration_body(value=category_id)
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    category = response.json()["data"][0]
    assert response.status_code == 200

    prepared_category_response = prepare_category_response(expected)
    prepared_expected_result = prepare_expected_result(category)

    for key in prepared_expected_result:
        assert prepared_category_response[key] == prepared_expected_result[key]


@mark.integration
@mark.parametrize(
    ["operator", "value", "expected"], [("lt", "11", 2), ("gt", "14", 10)]
)
def test_search_filter_gt_lt(
    operator, value, expected, prepare_db_categories_for_filtration
):
    data = prepare_filtration_body(operator=operator, value=value)
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    categories = response.json()["data"]
    assert response.status_code == 200
    assert len(categories) == expected


@mark.integration
@mark.parametrize(
    ["operator", "value", "expected"],
    [("like", "%T%1", 2), ("like", "%T%1_", 6), ("ilike", "%T%1_", 6)],
)
def test_search_filter_name_like(
    operator, value, expected, prepare_db_categories_for_filtration
):
    data = prepare_filtration_body(
        field="name", operator=operator, value=value
    )
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    categories = response.json()["data"]
    assert response.status_code == 200
    assert len(categories) == expected


@mark.integration
@mark.parametrize(["direction", "expected"], [("asc", "1"), ("desc", "4")])
def test_search_filter_ordering(
    direction, expected, prepare_db_categories_for_filtration
):
    data = prepare_filtration_body(
        operator="lt", value="5", direction=direction
    )
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    categories = response.json()["data"][0]
    assert response.status_code == 200
    assert categories["id"] == expected


@mark.integration
def test_search_filter_distinct_id(prepare_db_categories_for_filtration):
    data = prepare_filtration_body(
        page_size=30, field="id", operator="distinct"
    )
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    result_data = response.json()["data"]
    assert response.status_code == 200
    assert len(result_data) == 16


@mark.integration
def test_search_two_filters_different_distinct_order(
    prepare_db_categories_for_distinct_filtration,
):
    data = prepare_filtration_body_double_filter(
        first_field="type",
        second_field="editor",
        second_operator="is_not_null",
        sorting_field="type",
    )
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    first_result_data = response.json()["data"]
    data = prepare_filtration_body_double_filter(first_operator="is_not_null")
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    second_result_data = response.json()["data"]
    assert first_result_data == second_result_data


@mark.integration
def test_search_two_filters_both_distinct(
    prepare_db_categories_for_distinct_filtration,
):
    data = prepare_filtration_body_double_filter()
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    result_data = response.json()["data"]
    assert response.status_code == 200
    assert len(result_data) == 3


@mark.integration
def test_search_categories_400_error(prepare_db_categories_for_filtration):
    data = prepare_filtration_body(field="parent", operator="distinct")
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    error_message = (
        "SELECT DISTINCT ON expressions must "
        "match initial ORDER BY expressions"
    )
    assert response.status_code == 400
    assert error_message in response.text


@mark.integration
@mark.parametrize(
    ["wrong_parameter", "value"],
    [
        ("field", "wrong_field"),
        ("operator", "wrong_operator"),
        ("page_size", 0),
    ],
)
def test_search_wrong_parameters(
    wrong_parameter, value, prepare_db_categories_for_filtration
):
    data = prepare_filtration_body(**{wrong_parameter: value})
    response = client.post(
        f"{CATEGORIES_PATH}/search", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 422
    assert "value is not a valid enumeration member" in response.text


@mark.integration
@patch(
    "app.categories.resources.update_category_db", side_effect=SQLAlchemyError
)
def test_update_db_connection_error(prepare_db_categories_different_names):
    cat_id = 1
    data = prepare_category_body()
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@mark.integration
@mark.parametrize(
    "category_id",
    (3, 100),  # other tenant category and category that doesn't exist
)
def test_update_wrong_category(
    category_id,
    prepare_db_categories_different_names,
):
    data = prepare_category_body()
    response = client.put(
        f"{CATEGORIES_PATH}/{category_id}", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 404
    assert "Cannot update category that doesn't exist" in response.text


@mark.integration
def test_update_common_category(prepare_db_categories_different_names):
    cat_id = 2
    data = prepare_category_body()
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 400
    assert "Cannot update default category" in response.text


@mark.integration
@mark.parametrize(
    "field_value_pairs",
    [
        {"metadata": {"color": "blue"}},  # custom values in metadata field
        {"type": "segmentation"},  # custom values in is_link field
    ],
)
def test_update_category_custom_fields(
    field_value_pairs, prepare_db_categories_different_names
):
    cat_id = 1
    data = prepare_category_body(**field_value_pairs)
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 200
    assert prepare_expected_result(response.text) == prepare_category_response(
        data
    )


@mark.integration
@mark.parametrize(
    "category_name",
    ("Footer", "Table"),  # this tenant and common category already exist names
)
def test_update_exist_category_name(
    category_name,
    prepare_db_categories_different_names,
):
    cat_id = 1
    data_add = prepare_category_body(name="Footer")
    client.post(CATEGORIES_PATH, json=data_add, headers=TEST_HEADERS)
    data_update = prepare_category_body(name=category_name)
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data_update, headers=TEST_HEADERS
    )
    assert response.status_code == 400
    assert "Category name must be unique" in response.text


@mark.integration
def test_update_other_tenant_exist_name(prepare_db_categories_different_names):
    cat_id = 1
    data = prepare_category_body(name="Header")
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 200
    assert prepare_expected_result(response.text) == prepare_category_response(
        data
    )


@mark.integration
def test_update_self_parent(prepare_db_categories_different_names):
    cat_id = "1"
    data = prepare_category_body(parent="1")
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 400
    assert "Category cannot be its own parent." in response.text


@mark.integration
def test_update_self_parent_via_session(prepare_db_categories_different_names):
    category = Category(
        id="any",
        name="Any",
        tenant="test",
        parent="any",
        metadata_=None,
        type="box",
        editor=None,
        data_attributes=None,
    )
    prepare_db_categories_different_names.add(category)
    with pytest.raises(IntegrityError):
        prepare_db_categories_different_names.commit()
    prepare_db_categories_different_names.rollback()


@mark.integration
def test_update_other_tenant_parent(prepare_db_categories_different_names):
    cat_id = "1"
    data = prepare_category_body(parent="3")
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data, headers=TEST_HEADERS
    )
    assert response.status_code == 500
    assert "Foreign key error" in response.text


@mark.integration
@mark.parametrize(
    "category_parent",
    ("2", "4"),  # parent from commons and this tenant other category as parent
)
def test_update_allowed_parent(
    category_parent, prepare_db_categories_different_names
):
    cat_id = "1"
    data_add = prepare_category_body(name="Footer")
    data_add["id"] = category_parent
    prepare_db_categories_different_names.merge(
        Category(**clean_data_for_db(data_add))
    )
    prepare_db_categories_different_names.commit()
    data_update = prepare_category_body(parent=category_parent)
    response = client.put(
        f"{CATEGORIES_PATH}/{cat_id}", json=data_update, headers=TEST_HEADERS
    )
    assert response.status_code == 200
    assert prepare_expected_result(response.text) == prepare_category_response(
        data_update
    )


@mark.integration
@patch(
    "app.categories.resources.delete_category_db", side_effect=SQLAlchemyError
)
@patch("app.categories.resources.delete_taxonomy_link", Mock)
def test_delete_db_connection_error(prepare_db_categories_same_names):
    cat_id = "1"
    response = client.delete(
        f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@mark.integration
@mark.parametrize(
    "category_id",
    ("3", "100"),  # category from other tenant and category that doesn't exist
)
@patch("app.categories.resources.delete_taxonomy_link", Mock)
def test_delete_wrong_category(
    category_id,
    prepare_db_categories_same_names,
):
    cat_id = "100"
    response = client.delete(
        f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS
    )
    assert response.status_code == 404
    assert "Cannot delete category that doesn't exist" in response.text


@mark.integration
@patch("app.categories.resources.delete_taxonomy_link", Mock)
def test_delete_common_category(prepare_db_categories_same_names):
    cat_id = "2"
    response = client.delete(
        f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS
    )
    assert response.status_code == 400
    assert "Cannot delete default category" in response.text


@mark.integration
@patch("app.categories.resources.delete_taxonomy_link", Mock)
def test_delete_tenant_category(prepare_db_categories_same_names):
    cat_id = "1"
    response = client.delete(
        f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS
    )
    assert response.status_code == 204
    assert (
        client.get(
            f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS
        ).status_code
        == 404
    )


@mark.integration
@mark.parametrize("add_for_cascade_delete", ["1"], indirect=True)
@patch("app.categories.resources.delete_taxonomy_link", Mock)
def test_cascade_delete_tenant_parent(add_for_cascade_delete):
    cat_id = "1"
    child_1, child_2 = add_for_cascade_delete
    response = client.delete(
        f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS
    )
    assert response.status_code == 204
    assert (
        client.get(
            f"{CATEGORIES_PATH}/{cat_id}", headers=TEST_HEADERS
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{CATEGORIES_PATH}/{child_1}", headers=TEST_HEADERS
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{CATEGORIES_PATH}/{child_2}", headers=TEST_HEADERS
        ).status_code
        == 404
    )


@mark.integration
@mark.parametrize("add_for_cascade_delete", ["2"], indirect=True)
def test_cascade_delete_common_parent(add_for_cascade_delete):
    common_id = "2"
    child_1, child_2 = add_for_cascade_delete
    assert (
        client.get(
            f"{CATEGORIES_PATH}/{common_id}", headers=TEST_HEADERS
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{CATEGORIES_PATH}/{child_1}", headers=TEST_HEADERS
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{CATEGORIES_PATH}/{child_2}", headers=TEST_HEADERS
        ).status_code
        == 404
    )
