import asyncio
from typing import List
from unittest.mock import Mock, patch

import aiohttp
import elasticsearch
import pytest
import responses
from elasticsearch.exceptions import ElasticsearchException
from fastapi.testclient import TestClient

from search.config import settings
from search.es import NoSuchTenant, add_child_categories, build_query
from search.main import app

from .override_app_dependency import TEST_HEADERS, TEST_TENANT, TEST_TOKEN

TEST_OBJECTS_NUMBER = 10
TEST_DATA = [
    {
        "category": "category {0}".format(x),
        "content": "content {0}".format(x),
        "document_id": x,
        "page_number": x,
        "bbox": [float(x), float(x), float(x), float(x)],
        "job_id": 1,
        "tokens": None,
    }
    for x in range(1, TEST_OBJECTS_NUMBER + 1)
]
EXPECTED_OBJECT = [
    {
        "category": "category 1",
        "content": "content 1",
        "document_id": 1,
        "page_number": 1,
        "bbox": [1.0, 1.0, 1.0, 1.0],
        "job_id": 1,
        "tokens": None,
    }
]
PAGINATION_PAGE_SIZE = 5
PAGINATION_PAGE_NUM = 2
EXPECTED_PAGINATED_OBJECTS = TEST_DATA[5:]
CHILD_CATEGORIES_DATA = {
    "table_header": {
        "category": "table_header",
        "content": "table_header_content_1",
        "document_id": 1,
        "page_number": 101,
        "bbox": [101.0, 101.0, 101.0, 101.0],
        "job_id": 1,
        "tokens": None,
    },
    "table_cell": {
        "category": "table_cell",
        "content": "table_cell_content_1",
        "document_id": 2,
        "page_number": 102,
        "bbox": [102.0, 102.0, 102.0, 102.0],
        "job_id": 1,
        "tokens": None,
    },
    "table_cell_1": {
        "category": "table_cell_1",
        "content": "table_cell_content_2",
        "document_id": 2,
        "page_number": 102,
        "bbox": None,
        "job_id": 1,
        "tokens": ["token_1", "token_2"],
    },
    "table_cell_2": {
        "category": "table_cell_2",
        "content": "table_cell_content_3",
        "document_id": 3,
        "page_number": 103,
        "bbox": [103.0, 103.0, 103.0, 103.0],
        "job_id": 1,
        "tokens": None,
    },
}

client = TestClient(app)


@pytest.mark.integration
@pytest.mark.parametrize(
    (
        "url_params, expected_page_num, expected_page_size, "
        "expected_total_objects, expected_text_pieces"
    ),
    [
        ({}, 1, 50, 14, TEST_DATA + list(CHILD_CATEGORIES_DATA.values())),
        (
            {
                "page_size": PAGINATION_PAGE_SIZE,
                "page_num": PAGINATION_PAGE_NUM,
            },
            2,
            5,
            14,
            EXPECTED_PAGINATED_OBJECTS,
        ),
        ({"category": "category 1"}, 1, 50, 1, EXPECTED_OBJECT),
        ({"category": "category1"}, 1, 50, 0, []),
        (
            {"content": "content 1"},
            1,
            50,
            10,
            TEST_DATA,
        ),
        (
            {
                "content": "content 1",
                "page_size": PAGINATION_PAGE_SIZE,
                "page_num": PAGINATION_PAGE_NUM,
            },
            2,
            5,
            10,
            EXPECTED_PAGINATED_OBJECTS,
        ),
        ({"content": "content1"}, 1, 50, 0, []),
        (
            {"content": "content"},
            1,
            50,
            10,
            TEST_DATA,
        ),
        ({"page_number": 1}, 1, 50, 1, EXPECTED_OBJECT),
        (
            {"category": "category 1", "content": "content 1"},
            1,
            50,
            1,
            EXPECTED_OBJECT,
        ),
        ({"category": "category1", "content": "content1"}, 1, 50, 0, []),
        ({"category": "category1", "content": "content"}, 1, 50, 0, []),
        (
            {
                "category": "category 1",
                "content": "content 1",
                "document_id": 1,
                "page_number": 1,
            },
            1,
            50,
            1,
            EXPECTED_OBJECT,
        ),
        (
            {
                "category": "category 1",
                "content": "content",  # possible for 'match' content
                "document_id": 1,
                "page_number": 1,
            },
            1,
            50,
            1,
            EXPECTED_OBJECT,
        ),
        (
            {
                "category": "Category 1",  # wrong category for filter 'terms'
                "content": "content 1",
                "document_id": 1,
                "page_number": 1,
            },
            1,
            50,
            0,
            [],
        ),
        (
            {
                "category": "category 1",
                "content": "content 1",
                "document_id": 1,
                "page_number": 100,  # not exist number for filter 'term'
            },
            1,
            50,
            0,
            [],
        ),
        (
            {
                "category": "category 1",
                "content": "1",  # possible match (ES tokens: "content", "1")
                "document_id": 1,
                "page_number": 1,
            },
            1,
            50,
            1,
            EXPECTED_OBJECT,
        ),
    ],
)
def test_get_text_piece(
    index_test_data,
    url_params: dict,
    expected_page_num: int,
    expected_page_size: int,
    expected_total_objects: int,
    expected_text_pieces: List[dict],
):
    category_id = url_params.get("category", "")
    with patch("search.es.add_child_categories", return_value=[category_id]):
        response = client.get(
            settings.text_pieces_path,
            params=url_params,
            headers=TEST_HEADERS,
        )
        assert response.status_code == 200
        response = response.json()
        assert response["current_page"] == expected_page_num
        assert response["page_size"] == expected_page_size
        assert response["total_objects"] == expected_total_objects
        assert response["text_pieces"] == expected_text_pieces


@pytest.mark.asyncio
@pytest.mark.unittest
@pytest.mark.parametrize(
    "start_page, page_size, search_params,  expected_query",
    [
        (1, 50, {}, {"from": 0, "size": 50, "query": {"match_all": {}}}),
        (5, 50, {}, {"from": 200, "size": 50, "query": {"match_all": {}}}),
        (1, 10, {}, {"from": 0, "size": 10, "query": {"match_all": {}}}),
        (5, 10, {}, {"from": 40, "size": 10, "query": {"match_all": {}}}),
        (
            1,
            50,
            {"category": "test_category"},
            {
                "from": 0,
                "size": 50,
                "query": {
                    "bool": {
                        "filter": [{"terms": {"category": ["test_category"]}}],
                    },
                },
            },
        ),
        (
            1,
            50,
            {"page_number": 1},
            {
                "from": 0,
                "size": 50,
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "term": {"page_number": {"value": 1}},
                            }
                        ]
                    }
                },
            },
        ),
        (
            1,
            50,
            {"content": "test_content"},
            {
                "from": 0,
                "size": 50,
                "query": {
                    "bool": {"must": {"match": {"content": "test_content"}}},
                },
            },
        ),
        (
            1,
            50,
            {
                "content": "test_content",
                "page_number": 1,
                "category": "test_category",
            },
            {
                "from": 0,
                "size": 50,
                "query": {
                    "bool": {
                        "filter": [
                            {"terms": {"category": ["test_category"]}},
                            {"term": {"page_number": {"value": 1}}},
                        ],
                        "must": {"match": {"content": "test_content"}},
                    }
                },
            },
        ),
    ],
)
async def test_build_query(
    start_page: int,
    page_size: int,
    search_params: dict,
    expected_query: dict,
):
    with patch(
        "search.es.add_child_categories",
        return_value=[search_params.get("category", "")],
    ):
        resulted_query = await build_query(
            start_page, page_size, search_params, TEST_TENANT, TEST_TOKEN
        )
        assert resulted_query == expected_query


@pytest.mark.integration
@patch.object(elasticsearch.AsyncElasticsearch, "search")
def test_exception(search):
    url_params = {}
    search.side_effect = Mock(side_effect=ElasticsearchException())
    response = client.get(
        settings.text_pieces_path,
        params=url_params,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "url_params",
        "annotation_response",
        "expected_total_objects",
        "expected_text_pieces",
    ],
    [
        (
            {"category": "table_header"},
            [{"id": "table_header"}],
            1,
            [CHILD_CATEGORIES_DATA["table_header"]],
        ),
        (
            {"category": "table_cell"},
            [
                {"id": "table_cell"},
                {"id": "table_cell_1"},
                {"id": "table_cell_2"},
            ],
            3,
            [
                CHILD_CATEGORIES_DATA["table_cell"],
                CHILD_CATEGORIES_DATA["table_cell_1"],
                CHILD_CATEGORIES_DATA["table_cell_2"],
            ],
        ),
        (
            {"category": "table"},
            [
                {"id": "table_header"},
                {"id": "table_cell"},
                {"id": "table_cell_1"},
                {"id": "table_cell_2"},
            ],
            4,
            list(CHILD_CATEGORIES_DATA.values()),
        ),
    ],
)
@responses.activate
def test_get_child_categories(
    index_test_data,
    url_params: dict,
    annotation_response: List[dict],
    expected_total_objects: int,
    expected_text_pieces: List[dict],
):
    with patch(
        "search.es.add_child_categories", return_value=annotation_response
    ):
        response = client.get(
            settings.text_pieces_path,
            params=url_params,
            headers=TEST_HEADERS,
        )
        assert response.status_code == 200
        response = response.json()
        assert response["total_objects"] == expected_total_objects
        assert response["text_pieces"] == expected_text_pieces


@pytest.mark.integration
@pytest.mark.parametrize("tenant", ("wrong_tenant_1", "wrong_tenant_2"))
def test_no_such_tenant_index(tenant: str):
    headers = {
        "X-Current-Tenant": tenant,
        "Authorization": f"Bearer {TEST_TOKEN}",
    }
    with patch(
        "search.main.search",
        side_effect=NoSuchTenant(f"Index for tenant {tenant} doesn't exist"),
    ):
        response = client.get(
            settings.text_pieces_path,
            headers=headers,
        )
        assert response.status_code == 404
        assert f"Index for tenant {tenant} doesn't exist" in response.text


@pytest.mark.asyncio
@pytest.mark.unittest
@pytest.mark.parametrize(
    "child_categories", [("category_1", "category_2"), tuple()]
)
async def test_add_child_categories(child_categories):
    with patch(
        "search.es.fetch",
        return_value=(
            200,
            [{"id": category_id} for category_id in child_categories],
        ),
    ):
        category_id = "category"
        expected_categories = [*child_categories, category_id]
        categories_ids = await add_child_categories(
            category_id, TEST_TENANT, TEST_TOKEN
        )
        assert categories_ids == expected_categories


@pytest.mark.integration
@pytest.mark.parametrize(
    ["annotation_status", "search_status"],
    [(404, 500), (422, 500), (429, 500), (500, 500), (503, 500)],
)
@responses.activate
def test_annotation_connection_errors(
    index_test_data, annotation_status, search_status
):
    category_id = "category 1"
    annotation_child_categories_url = (
        f"{settings.annotation_categories_url}/{category_id}/child"
    )
    responses.add(
        responses.GET,
        annotation_child_categories_url,
        json={"detail": "Error message"},
        headers=TEST_HEADERS,
        status=annotation_status,
    )
    response = client.get(
        settings.text_pieces_path,
        params={"category": category_id},
        headers=TEST_HEADERS,
    )
    assert response.status_code == search_status
    if response.status_code == 500:
        assert f"Can't get subcategories for {category_id}" in response.text


@pytest.mark.integration
def test_requests_exception(monkeypatch):
    error_message = "some error"
    category_id = "category 1"
    monkeypatch.setattr(
        "search.es.fetch",
        Mock(side_effect=aiohttp.ClientError(error_message)),
    )
    url_params = {"category": category_id}
    response = client.get(
        settings.text_pieces_path,
        params=url_params,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    expected_error_response = (
        f"Can't get subcategories for {category_id} "
        f"due to error {error_message}"
    )
    assert expected_error_response in response.text


@pytest.mark.unittest
def test_facets_endpoint():
    mock_es_query = {"facets": []}
    es_response = {
        "aggregations": {
            "category": {
                "category": {
                    "buckets": [
                        {"key": "Header", "doc_count": 10},
                        {"key": "Title", "doc_count": 10},
                    ]
                }
            }
        }
    }
    with patch(
        "search.main.es.ES.search", return_value=asyncio.Future()
    ) as mock:
        with patch(
            "search.main.schemas.facets.FacetsResponse.adjust_facet_result",
            return_value=asyncio.Future(),
        ) as mock1:
            mock.return_value.set_result(es_response)
            mock1.return_value.set_result(None)
            resp = client.post(
                "/facets", json=mock_es_query, headers=TEST_HEADERS
            )
            assert resp.json() == {
                "facets": [
                    {
                        "name": "category",
                        "values": [
                            {"id": "Header", "count": 10, "name": None},
                            {"id": "Title", "count": 10, "name": None},
                        ],
                    }
                ]
            }
