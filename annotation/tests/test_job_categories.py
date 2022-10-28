from typing import List, Optional, Tuple
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
) -> dict:
    categories = []
    for cat_id, cat_name in categories_ids_names:
        category = prepare_category_body(name=cat_name)
        category["id"] = cat_id
        categories.append(category)
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
    expected_result = prepare_get_result([(cat_id, cat_name)], total_objects=1)
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
