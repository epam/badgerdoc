from typing import List
from unittest.mock import Mock, patch

import pytest
import responses
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
)
from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from annotation.models import Category
from annotation.schemas import CategoryTypeSchema
from tests.consts import CATEGORIES_PATH, POST_JOBS_PATH
from tests.override_app_dependency import (
    TEST_HEADERS,
    TEST_TENANT,
    TEST_TOKEN,
    app,
)
from tests.test_job_categories import prepare_job_body
from tests.test_post_next_task import ASSETS_RESPONSE

#  Cyclic categories have tree hierarchical structure of ids:
#  "1" -> "2" -> "4" -> "1"
#   '- -> "3"
TEST_TYPE = CategoryTypeSchema.box

CYCLIC_TENANT_CHILD_CATEGORIES = (
    Category(id="1", name="1", tenant=TEST_TENANT, type=TEST_TYPE),
    Category(id="2", name="2", parent="1", tenant=TEST_TENANT, type=TEST_TYPE),
    Category(id="3", name="3", parent="1", tenant=TEST_TENANT, type=TEST_TYPE),
    Category(id="4", name="4", parent="2", tenant=TEST_TENANT, type=TEST_TYPE),
)

OTHER_TENANT_CHILD_CATEGORY = Category(
    id="5", name="5", tenant="other", type=TEST_TYPE
)
NOT_EXIST_ID = "100"

#  Common categories have tree hierarchical structure of ids:
#  "6" -> "7" -> "8" -> "10" -> "11"
#          '- -> "9" -> "12" -> "13"
#                         '- -> "14"

COMMON_CHILD_CATEGORIES = (
    Category(id="6", name="6", type=TEST_TYPE),
    Category(id="7", name="7", parent="6", type=TEST_TYPE),
    Category(id="8", name="8", parent="7", type=TEST_TYPE),
    Category(id="9", name="9", parent="7", type=TEST_TYPE),
    Category(id="10", name="10", parent="8", type=TEST_TYPE),
    Category(id="11", name="11", parent="10", type=TEST_TYPE),
    Category(id="12", name="12", parent="9", type=TEST_TYPE),
    Category(id="13", name="13", parent="12", type=TEST_TYPE),
    Category(id="14", name="14", parent="12", type=TEST_TYPE),
)

client = TestClient(app)


def make_response(category_ids: List[str]) -> List[dict]:
    return [{"id": category_id} for category_id in category_ids]


@pytest.mark.integration
@patch.object(Session, "query")
@pytest.mark.skip(reason="tests refactoring")
def test_db_connection_error(Session, prepare_db_child_categories):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    category_id = "1"
    response = client.get(
        f"{CATEGORIES_PATH}/{category_id}/child",
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["root_category", "expected_subcategories", "tenant"],
    [
        ("1", make_response(["2", "3", "4"]), TEST_TENANT),
        ("3", [], TEST_TENANT),
        ("4", make_response(["1", "2", "3"]), TEST_TENANT),
        (
            "6",
            make_response(["10", "11", "12", "13", "14", "7", "8", "9"]),
            TEST_TENANT,
        ),
        ("9", make_response(["12", "13", "14"]), TEST_TENANT),
        ("12", make_response(["13", "14"]), TEST_TENANT),
        ("5", [], "other"),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_get_child_categories(
    prepare_db_child_categories,
    root_category,
    expected_subcategories,
    tenant,
):
    response = client.get(
        f"{CATEGORIES_PATH}/{root_category}/child",
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 200
    assert response.json() == expected_subcategories


@pytest.mark.integration
@pytest.mark.parametrize(
    ["category_id", "tenant"],
    [("1", "other"), ("5", TEST_TENANT), (NOT_EXIST_ID, TEST_TENANT)],
)
@pytest.mark.skip(reason="tests refactoring")
def test_get_wrong_categories(
    prepare_db_child_categories, category_id, tenant
):
    response = client.get(
        f"{CATEGORIES_PATH}/{category_id}/child",
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 404
    assert f"Category with id: {category_id} doesn't exist" in response.text


@pytest.mark.integration
@pytest.mark.skip(reason="tests refactoring")
def test_get_child_categories_cache(
    prepare_db_child_categories, prepare_child_categories_cache
):
    assert prepare_child_categories_cache.currsize == 0
    client.get(
        f"{CATEGORIES_PATH}/1/child",
        headers=TEST_HEADERS,
    )
    assert prepare_child_categories_cache.currsize == 4


@responses.activate
@pytest.mark.integration
@pytest.mark.skip(reason="tests refactoring")
def test_get_child_categories_cache_stays_intact_when_new_job_created(
    prepare_db_child_categories, prepare_child_categories_cache
):
    client.get(
        f"{CATEGORIES_PATH}/1/child",
        headers=TEST_HEADERS,
    )
    cache_size_after_request = prepare_child_categories_cache.currsize
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    client.post(
        f"{POST_JOBS_PATH}/1",
        data=prepare_job_body(categories=["1"]),
        headers=TEST_HEADERS,
    )
    cache_size_after_new_job_create = prepare_child_categories_cache.currsize
    assert cache_size_after_request == cache_size_after_new_job_create
