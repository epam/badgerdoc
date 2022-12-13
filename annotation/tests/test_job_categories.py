from json import loads
from typing import Any, List, Optional, Tuple, Union
from uuid import UUID

from fastapi.testclient import TestClient
from pytest import mark
from sqlalchemy.orm import Session

from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.models import Category, Job
from app.schemas import JobTypeEnumSchema, ValidationSchema
from tests.consts import POST_JOBS_PATH
from tests.override_app_dependency import (
    TEST_HEADERS,
    TEST_TENANT,
    TEST_TOKEN,
    app,
)
from tests.test_category_crud import prepare_category_body

JOBS_PATH = "/jobs"
MOCK_ID = 1
CATEGORIES_USERS = [
    "7303e478-8a71-44f2-acb1-8dafe5116b4c",
    "7303e478-8a71-44f2-acb1-8dafe5116b4d",
]

client = TestClient(app)


NOT_FULLY_TEST_SUPPORTED_CATEGORY_ATTRIBUTES = (
    "parents",
    "is_leaf",
    "id",
)


def prepare_job_body(
    categories: List[str],
    callback_url: Optional[str] = "http://datasetmanager.com",
    annotators: List[UUID] = None,
    validators: List[UUID] = None,
    owners: List[UUID] = None,
    validation_type: ValidationSchema = ValidationSchema.cross.value,
    files: Optional[str] = MOCK_ID,
    is_auto_distribution: Optional[bool] = False,
    job_type: Optional[JobTypeEnumSchema] = JobTypeEnumSchema.AnnotationJob,
) -> dict:
    body = {
        "callback_url": callback_url,
        "annotators": CATEGORIES_USERS if annotators is None else annotators,
        "validators": [] if validators is None else validators,
        "owners": [] if owners is None else owners,
        "validation_type": validation_type,
        "files": [files],
        "datasets": [],
        "is_auto_distribution": is_auto_distribution,
        "categories": categories,
        "tenant": TEST_TENANT,
        "job_type": job_type,
    }
    return body


def prepare_get_result(
    categories_ids_names: List[Tuple[str, str]],
    current_page: Optional[int] = 1,
    page_size: Optional[int] = 50,
    total_objects: Optional[int] = 16,
    parents=None,
    is_leaf=None,
) -> dict:
    categories = []
    for cat_id, cat_name in categories_ids_names:
        category = prepare_category_body(name=cat_name)
        category["id"] = cat_id
        category["parents"] = parents
        category["is_leaf"] = is_leaf
        categories.append(category),
    body = {
        "pagination": {
            "page_num": current_page,
            "page_size": page_size,
            "min_pages_left": 1,
            "total": total_objects,
            "has_more": False,
        },
        "data": categories,
    }
    return body


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


@mark.integration
@mark.parametrize(
    ["cat_ids", "cat_tenant"],
    [
        (["1"], TEST_TENANT),  # category with the same tenant
        (["1", "1", "1"], TEST_TENANT),  # repeated category, same tenant
        (["3"], None),  # common category (access for all tenants)
    ],
)
def test_job_available_categories(
    cat_ids,
    cat_tenant,
    mock_assets_communication,
):
    session = mock_assets_communication
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}",
        json=prepare_job_body(categories=cat_ids),
        headers=TEST_HEADERS,
    )
    job = session.query(Job).get(MOCK_ID)
    categories = job.categories
    assert response.status_code == 201
    assert len(categories) == 1
    assert categories[0].id == cat_ids[0]
    assert categories[0].tenant == cat_tenant


@mark.integration
def test_job_no_categories(mock_assets_communication):
    session = mock_assets_communication
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}",
        json=prepare_job_body(categories=[]),
        headers=TEST_HEADERS,
    )
    error_message = "There should be not less than one category provided"
    job = session.query(Job).get(MOCK_ID)
    assert response.status_code == 422
    assert error_message in response.text
    assert not job


@mark.integration
@mark.parametrize(
    ["cat_ids", "request_tenant", "expected_cat_ids"],
    [
        (
            ["100", "200"],
            TEST_TENANT,
            "100, 200",
        ),  # single not exist category
        (
            ["1", "100", "5"],
            TEST_TENANT,
            "100",
        ),  # not exist one of categories
        (["2"], TEST_TENANT, "2"),  # category of other tenant
        (["1"], "other_tenant", "1"),  # category of other tenant
    ],
)
def test_job_wrong_category(
    cat_ids,
    request_tenant,
    expected_cat_ids,
    mock_assets_communication,
):
    session = mock_assets_communication
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}",
        json=prepare_job_body(categories=cat_ids),
        headers={
            HEADER_TENANT: request_tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    job = session.query(Job).get(MOCK_ID)
    assert response.status_code == 404
    assert f"No such categories: {expected_cat_ids}" in response.text
    assert not job


@mark.integration
def test_job_category_db_error(mock_db_error_for_job_categories):
    session = mock_db_error_for_job_categories
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}",
        json=prepare_job_body(categories=["1"]),
        headers=TEST_HEADERS,
    )
    job = session.query(Job).get(MOCK_ID)
    assert response.status_code == 500
    assert "Error: connection error" in response.text
    assert not job


def delete_category(session: Session, cat_id: str) -> None:
    category = session.query(Category).get(cat_id)
    session.delete(category)
    session.commit()
    return session.query(Category).get(cat_id)


def delete_job(session: Session, job_id: int) -> None:
    job = session.query(Job).get(job_id)
    f = job.files[0]
    session.delete(f)
    session.delete(job)
    session.commit()
    return session.query(Job).get(job_id)


@mark.integration
def test_delete_categories_no_cascade(mock_assets_communication):
    session = mock_assets_communication
    client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}",
        json=prepare_job_body(categories=["1"]),
        headers=TEST_HEADERS,
    )
    job = session.query(Job).get(MOCK_ID)
    categories = job.categories
    assert len(categories) == 1
    assert not delete_category(session, "1")
    assert session.query(Job).get(MOCK_ID)


@mark.integration
def test_get_job_via_category(mock_assets_communication):
    session = mock_assets_communication
    client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}",
        json=prepare_job_body(categories=["1"]),
        headers=TEST_HEADERS,
    )
    category = session.query(Category).get("1")
    job = session.query(Job).get(MOCK_ID)
    assert category.jobs[0] == job


@mark.integration
def test_delete_job_no_cascade(mock_assets_communication):
    session = mock_assets_communication
    client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}",
        json=prepare_job_body(categories=["1"]),
        headers=TEST_HEADERS,
    )
    job = session.query(Job).get(MOCK_ID)
    categories = job.categories
    assert len(categories) == 1
    assert not delete_job(session, MOCK_ID)
    assert session.query(Category).get("1")


@mark.integration
@mark.parametrize(
    ["job_id", "request_tenant"],
    [
        (2, TEST_TENANT),  # not exist job
        (MOCK_ID, "other_tenant"),  # other tenant's job
    ],
)
def test_get_job_categories_wrong_job(
    prepare_db_job_with_filter_categories,
    job_id,
    request_tenant,
):
    response = client.get(
        f"{JOBS_PATH}/{job_id}/categories",
        headers={
            HEADER_TENANT: request_tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 404
    assert f"Job with job_id ({job_id}) not found" in response.text


@mark.integration
@mark.parametrize(
    ["prepare_db_job_with_single_category", "cat_id", "cat_name"],
    [
        ("1", "1", "Title"),  # this tenant category
        ("3", "3", "Table1"),  # common category
    ],
    indirect=["prepare_db_job_with_single_category"],
)
def test_get_job_categories_tenant(
    prepare_db_job_with_single_category,
    cat_id,
    cat_name,
):
    response = client.get(
        f"{JOBS_PATH}/{MOCK_ID}/categories",
        headers=TEST_HEADERS,
    )
    expected_result = prepare_get_result(
        [(cat_id, cat_name)], total_objects=1, parents=None, is_leaf=None
    )
    assert response.status_code == 200
    assert response.json() == expected_result


@mark.integration
@mark.parametrize(
    ["page_size", "page_num", "expected_results_count"],  # 16 results total
    [
        (15, 1, 15),
        (30, 1, 16),
        (15, 2, 1),
    ],
)
def test_get_job_categories_pagination(
    prepare_db_job_with_filter_categories,
    page_size,
    page_num,
    expected_results_count,
):
    pagination_params = {"page_size": page_size, "page_num": page_num}
    response = client.get(
        f"{JOBS_PATH}/{MOCK_ID}/categories",
        headers=TEST_HEADERS,
        params=pagination_params,
    )
    categories = response.json()["data"]
    pagination = response.json()["pagination"]
    assert pagination["page_num"] == page_num
    assert pagination["page_size"] == page_size
    assert pagination["total"] == 16
    assert len(categories) == expected_results_count


@mark.integration
@mark.parametrize("page_size", (20, 1, 10))
def test_get_job_wrong_pagination(
    page_size, prepare_db_job_with_filter_categories
):
    pagination_params = {"page_size": page_size, "page_num": 1}
    response = client.get(
        f"{JOBS_PATH}/{MOCK_ID}/categories",
        headers=TEST_HEADERS,
        params=pagination_params,
    )
    assert response.status_code == 422
    assert "value is not a valid enumeration member" in response.text


@mark.integration
@mark.parametrize(
    ["page_num", "page_size", "result_length"],
    [(1, 15, 15), (2, 15, 1), (3, 15, 0), (1, 30, 16)],
)
def test_search_pagination(
    page_num,
    page_size,
    result_length,
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(
        page_num=page_num, page_size=page_size, no_filtration=True
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    categories = response.json()["data"]
    pagination = response.json()["pagination"]
    assert response.status_code == 200
    assert pagination["total"] == 16
    assert pagination["page_num"] == page_num
    assert pagination["page_size"] == page_size
    assert len(categories) == result_length


@mark.integration
def test_search_no_filtration(
    prepare_db_categories_for_filtration, prepare_db_job_with_filter_categories
):
    data = prepare_filtration_body(page_size=30, no_filtration=True)
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
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
    category_id,
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(value=category_id)
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
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
    prepare_db_job_with_filter_categories,
):
    expected = prepare_category_body(name=category_name)
    data = prepare_filtration_body(value=category_id)
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    category = response.json()["data"][0]
    assert response.status_code == 200
    assert prepare_expected_result(category) == prepare_category_response(
        expected
    )


@mark.integration
@mark.parametrize(
    ["operator", "value", "expected"], [("lt", "11", 2), ("gt", "14", 10)]
)
def test_search_filter_gt_lt(
    operator,
    value,
    expected,
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(operator=operator, value=value)
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
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
    operator,
    value,
    expected,
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(
        field="name", operator=operator, value=value
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    categories = response.json()["data"]
    assert response.status_code == 200
    assert len(categories) == expected


@mark.integration
@mark.parametrize(["direction", "expected"], [("asc", "1"), ("desc", "4")])
def test_search_filter_ordering(
    direction,
    expected,
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(
        operator="lt", value="5", direction=direction
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    categories = response.json()["data"][0]
    assert response.status_code == 200
    assert categories["id"] == expected


@mark.integration
def test_search_filter_distinct_id(
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(
        page_size=30, field="id", operator="distinct"
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    result_data = response.json()["data"]
    assert response.status_code == 200
    assert len(result_data) == 16


@mark.integration
def test_search_two_filters_different_distinct_order(
    prepare_db_categories_for_distinct_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body_double_filter(
        first_field="type",
        second_field="editor",
        second_operator="is_not_null",
        sorting_field="type",
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    first_result_data = response.json()["data"]
    data = prepare_filtration_body_double_filter(first_operator="is_not_null")
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    second_result_data = response.json()["data"]
    assert first_result_data == second_result_data


@mark.integration
def test_search_two_filters_both_distinct(
    prepare_db_categories_for_distinct_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body_double_filter()
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    result_data = response.json()["data"]
    assert response.status_code == 200
    assert len(result_data) == 3


@mark.integration
def test_search_categories_400_error(
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(field="parent", operator="distinct")
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
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
    wrong_parameter,
    value,
    prepare_db_categories_for_filtration,
    prepare_db_job_with_filter_categories,
):
    data = prepare_filtration_body(**{wrong_parameter: value})
    response = client.post(
        f"{POST_JOBS_PATH}/{MOCK_ID}/categories/search",
        json=data,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 422
    assert "value is not a valid enumeration member" in response.text
