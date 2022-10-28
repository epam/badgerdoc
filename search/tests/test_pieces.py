from unittest.mock import patch

import pytest

import search.schemas.pieces as pieces


class TestData:
    pagination = {"page_num": 1, "page_size": 10}
    filter_1 = {"field": "category", "operator": "eq", "value": "Header"}
    filter_2 = {
        "field": "category",
        "operator": "not_in",
        "value": ["Header", "Table"],
    }
    sort = {"field": "category", "direction": "asc"}
    request_1 = {
        "query": "some",
        "pagination": {"page_num": 1, "page_size": 50},
        "filters": [
            {"field": "category", "operator": "eq", "value": "Table"},
            {"field": "job_id", "operator": "eq", "value": "10"},
        ],
        "sorting": [
            {"field": "category", "direction": "asc"},
            {"field": "job_id", "direction": "desc"},
        ],
    }
    request_2 = {
        "query": "Elastic",
        "filters": [
            {
                "field": "category",
                "operator": "in",
                "value": ["Football", "Basketball", "Software Development"],
            },
            {"field": "job_id", "operator": "in", "value": [123, 1234, 12]},
            {
                "field": "page_number",
                "operator": "not_in",
                "value": [10000, 1000000],
            },
        ],
        "sorting": [
            {"field": "category", "direction": "asc"},
            {"field": "job_id", "direction": "desc"},
        ],
    }
    es_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_source": {
                        "category": "Table",
                        "content": "Text",
                        "job_id": 1,
                        "document_id": 1,
                        "page_number": 1,
                        "bbox": None,
                        "tokens": None,
                    }
                }
            ],
        }
    }


@pytest.mark.unittest
def test_pagination():
    pag = pieces.PiecePagination.validate(TestData.pagination)
    assert pag.build_pagination_body() == {"from": 0, "size": 10}


@pytest.mark.unittest
def test_filter_eq():
    fil = pieces.PieceFilter.validate(TestData.filter_1)
    assert fil.is_include
    assert fil.get_filter_template() == {"terms": {"category": ["Header"]}}


@pytest.mark.unittest
def test_filter_not_in():
    fil = pieces.PieceFilter.validate(TestData.filter_2)
    assert not fil.is_include
    assert fil.get_filter_template() == {
        "terms": {"category": ["Header", "Table"]}
    }


@pytest.mark.unittest
def test_sort():
    sort_ = pieces.PieceSort.validate(TestData.sort)
    assert sort_.build_sorting_body() == {"category": {"order": "asc"}}


@pytest.mark.unittest
def test_request_1():
    req = pieces.PiecesRequest.validate(TestData.request_1)
    assert req.build_query() == {
        "query": {
            "bool": {
                "must": [
                    {"terms": {pieces.PIECES_ENUM.CATEGORY: ["Table"]}},
                    {"terms": {pieces.PIECES_ENUM.JOB_ID: [10]}},
                    {
                        "match": {
                            "content": {
                                "minimum_should_match": "81%",
                                "query": TestData.request_1["query"],
                            }
                        }
                    },
                ],
                "must_not": [],
            }
        },
        "from": 0,
        "size": 50,
        "sort": [
            {
                pieces.PIECES_ENUM.CATEGORY: {
                    "order": pieces.PieceSortDirections.ASC
                }
            },
            {
                pieces.PIECES_ENUM.JOB_ID: {
                    "order": pieces.PieceSortDirections.DESC
                }
            },
        ],
    }


@pytest.mark.unittest
def test_request_2():
    req = pieces.PiecesRequest.validate(TestData.request_2)
    assert req.build_query() == {
        "query": {
            "bool": {
                "must": [
                    {
                        "terms": {
                            pieces.PIECES_ENUM.CATEGORY: [
                                "Football",
                                "Basketball",
                                "Software Development",
                            ]
                        }
                    },
                    {"terms": {pieces.PIECES_ENUM.JOB_ID: [123, 1234, 12]}},
                    {
                        "match": {
                            "content": {
                                "minimum_should_match": "81%",
                                "query": TestData.request_2["query"],
                            }
                        }
                    },
                ],
                "must_not": [
                    {
                        "terms": {
                            pieces.PIECES_ENUM.PAGE_NUMBER: [10000, 1000000]
                        }
                    }
                ],
            }
        },
        "from": 0,
        "size": 50,
        "sort": [
            {
                pieces.PIECES_ENUM.CATEGORY: {
                    "order": pieces.PieceSortDirections.ASC
                }
            },
            {
                pieces.PIECES_ENUM.JOB_ID: {
                    "order": pieces.PieceSortDirections.DESC
                }
            },
        ],
    }


@pytest.mark.asyncio
@pytest.mark.unittest
async def test_adjust_categories():
    filter_ = pieces.PieceFilter.validate(TestData.filter_1)
    with patch(
        "search.es.add_child_categories", return_value=["Table", "Cell"]
    ):
        await filter_.adjust_for_child_categories("foo", "bar")
        assert sorted(filter_.value) == sorted(["Header", "Table", "Cell"])


@pytest.mark.unittest
def test_parse_es_response():
    pag = pieces.PiecePagination(page_num=1, page_size=10)
    resp = pieces.SearchResultSchema2.parse_es_response(
        TestData.es_response, pag
    )
    assert resp.dict() == {
        "pagination": {"page_num": 1, "page_size": 10, "total": 1, "pages": 1},
        "data": [
            {
                "category": "Table",
                "content": "Text",
                "document_id": 1,
                "page_number": 1,
                "job_id": 1,
                "bbox": None,
                "tokens": None,
            }
        ],
    }
