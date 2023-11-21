from unittest.mock import patch

import pydantic
import pytest

import search.schemas.facets as facets


class TestData:
    valid_filter_params_in = {
        "field": "category",
        "operator": "in",
        "value": ["Title", "Header"],
    }
    wrong_field_filter_params = {
        "field": "some",
        "operator": "in",
        "value": ["Title", "Header"],
    }
    wrong_operator_filter_params = {
        "field": "category",
        "operator": "eq",
        "value": ["Title", "Header"],
    }
    valid_facet_params = {"name": "category", "limit": 10}
    wrong_facet_params = {"name": "some", "limit": 10}
    valid_facet_request_1 = {
        "query": "Elasticsearch",
        "facets": [
            {"name": "category", "limit": 10},
            {"name": "job_id", "limit": 10},
        ],
        "filters": [
            {
                "field": "category",
                "operator": "in",
                "value": ["Header", "Title"],
            },
            {
                "field": "job_id",
                "operator": "not_in",
                "value": [10, 100],
            },
            {"field": "page_number", "operator": "in", "value": [1, 2]},
        ],
    }
    valid_facet_request_2 = {"facets": [{"name": "category", "limit": 5}]}
    wrong_facet_request_2 = {
        "query": "some",
        "facets": [{"name": "some", "limit": 5}],
        "filters": [{"field": "some", "operator": "in", "value": ["some1", "some2"]}],
    }
    agg_result_1 = {"key": "Header", "doc_count": 10}
    agg_result_2 = {"key": "Title", "doc_count": 10}
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


@pytest.mark.unittest
def test_filter_params_schema_pos():
    assert facets.FilterParams.validate(TestData.valid_filter_params_in)


@pytest.mark.unittest
def test_filter_params_schema_neg():
    with pytest.raises(pydantic.ValidationError):
        facets.FilterParams.parse_obj(TestData.wrong_field_filter_params)
    with pytest.raises(pydantic.ValidationError):
        facets.FilterParams.parse_obj(TestData.wrong_operator_filter_params)


@pytest.mark.unittest
def test_filter_param_template():
    obj = facets.FilterParams.parse_obj(TestData.valid_filter_params_in)
    assert obj.filter_template == {
        "terms": {
            TestData.valid_filter_params_in["field"]: TestData.valid_filter_params_in[
                "value"
            ]
        }
    }


@pytest.mark.unittest
def test_facet_params_schema_pos():
    assert facets.FacetParams.validate(TestData.valid_facet_params)


@pytest.mark.unittest
def test_facet_params_schema_neg():
    with pytest.raises(pydantic.ValidationError):
        facets.FacetParams.validate(TestData.wrong_facet_params)


@pytest.mark.unittest
def test_facet_params_facet_template():
    obj = facets.FacetParams.parse_obj(TestData.valid_facet_params)
    assert obj.facet_template == {
        TestData.valid_facet_params["name"]: {
            "filter": {"bool": {"must": [], "must_not": []}},
            "aggs": {
                TestData.valid_facet_params["name"]: {
                    "terms": {
                        "field": TestData.valid_facet_params["name"],
                        "size": TestData.valid_facet_params["limit"],
                    }
                }
            },
        }
    }


@pytest.mark.unittest
def test_facet_request_schema_pos():
    assert facets.FacetsRequest.validate(TestData.valid_facet_request_1)
    assert facets.FacetsRequest.validate(TestData.valid_facet_request_2)


@pytest.mark.unittest
def test_facet_request_schema_neg():
    with pytest.raises(pydantic.ValidationError):
        facets.FacetsRequest.validate(TestData.wrong_facet_request_2)


@pytest.mark.unittest
def test_facet_request_build_es_query():
    obj_1 = facets.FacetsRequest.parse_obj(TestData.valid_facet_request_1)
    assert obj_1.build_es_query() == {
        "aggs": {
            "category": {
                "filter": {
                    "bool": {
                        "must": [{"terms": {"page_number": [1, 2]}}],
                        "must_not": [{"terms": {"job_id": [10, 100]}}],
                    }
                },
                "aggs": {"category": {"terms": {"field": "category", "size": 10}}},
            },
            "job_id": {
                "filter": {
                    "bool": {
                        "must": [
                            {"terms": {"category": ["Header", "Title"]}},
                            {"terms": {"page_number": [1, 2]}},
                        ],
                        "must_not": [],
                    }
                },
                "aggs": {
                    "job_id": {
                        "terms": {
                            "field": "job_id",
                            "size": 10,
                        }
                    },
                },
            },
        },
        "size": 0,
        "query": {
            "match": {
                "content": {
                    "query": "Elasticsearch",
                    "minimum_should_match": "81%",
                }
            }
        },
    }

    obj_2 = facets.FacetsRequest.parse_obj(TestData.valid_facet_request_2)
    assert obj_2.build_es_query() == {
        "aggs": {
            "category": {
                "filter": {"bool": {"must": [], "must_not": []}},
                "aggs": {"category": {"terms": {"field": "category", "size": 5}}},
            }
        },
        "size": 0,
    }


@pytest.mark.unittest
def test_agg_result_schema():
    obj = facets.AggResult.parse_es_agg_doc(TestData.agg_result_1)
    assert obj.dict() == {"id": "Header", "count": 10, "name": None}


@pytest.mark.unittest
def test_facet_response_body_schema():
    agg_1 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_1)
    agg_2 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_2)
    obj = facets.FacetBodyResponse(name="category", values=[agg_1, agg_2])
    assert obj.dict() == {
        "name": "category",
        "values": [
            {"id": "Header", "count": 10, "name": None},
            {"id": "Title", "count": 10, "name": None},
        ],
    }


@pytest.mark.unittest
def test_facet_response():
    obj = facets.FacetsResponse.parse_es_response(TestData.es_response)
    assert obj.dict() == {
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


@pytest.mark.unittest
def test_update_data():
    agg_1 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_1)
    agg_2 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_2)
    obj = facets.FacetBodyResponse(name="category", values=[agg_1, agg_2])
    data = {
        "data": [
            {"id": "Header", "name": "Header_name"},
            {"id": "Title", "name": "Title_name"},
            {"id": "Some", "name": "Some_name"},
        ]
    }
    obj.update_data(data)
    assert obj.dict() == {
        "name": "category",
        "values": [
            {"id": "Header", "count": 10, "name": "Header_name"},
            {"id": "Title", "count": 10, "name": "Title_name"},
        ],
    }


@pytest.mark.unittest
@pytest.mark.asyncio
async def test_adjust_facet():
    agg_1 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_1)
    agg_2 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_2)
    obj = facets.FacetBodyResponse(name="category", values=[agg_1, agg_2])
    data = {
        "data": [
            {"id": "Header", "name": "Header_name"},
            {"id": "Title", "name": "Title_name"},
            {"id": "Some", "name": "Some_name"},
        ]
    }
    with patch(
        "search.schemas.facets.FacetBodyResponse.fetch_data",
        return_value=data,
    ):
        await obj.adjust_facet("tenant", "token")
        assert obj.dict() == {
            "name": "category",
            "values": [
                {"id": "Header", "count": 10, "name": "Header_name"},
                {"id": "Title", "count": 10, "name": "Title_name"},
            ],
        }


@pytest.mark.unittest
@pytest.mark.asyncio
async def test_adjust_facet_result():
    agg_1 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_1)
    agg_2 = facets.AggResult.parse_es_agg_doc(TestData.agg_result_2)
    resp = facets.FacetBodyResponse(name="category", values=[agg_1, agg_2])
    obj = facets.FacetsResponse(facets=[resp])
    data = {
        "data": [
            {"id": "Header", "name": "Header_name"},
            {"id": "Title", "name": "Title_name"},
            {"id": "Some", "name": "Some_name"},
        ]
    }
    with patch(
        "search.schemas.facets.FacetBodyResponse.fetch_data",
        return_value=data,
    ):
        await obj.adjust_facet_result("tenant", "token")
        assert obj.dict() == {
            "facets": [
                {
                    "name": "category",
                    "values": [
                        {"id": "Header", "count": 10, "name": "Header_name"},
                        {"id": "Title", "count": 10, "name": "Title_name"},
                    ],
                }
            ]
        }
