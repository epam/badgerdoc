from ..src.dict_parser import map_request_to_filter


example_1 = {
    "pagination": {"page_num": 1, "page_size": 50},
    "filters": [
        {"field": "ts_vector", "operator": "match", "value": "kubeflow"}
    ],
    "sorting": [{"field": "id", "direction": "desc"}],
}

example_2 = {
    "pagination": {"page_num": 1, "page_size": 50},
    "filters": [
        {"field": "ts_vector", "operator": "match", "value": "kubeflow"},
        {"field": "original_name", "operator": "eq", "value": "epam"},
        {"field": "pages", "operator": "gt", "value": 100},
    ],
    "sorting": [{"field": "created", "direction": "desc"}],
}

example_3 = {
    "pagination123": {"page_num": 1, "page_size": 50},
    "filters123": [
        {"field": "ts_vector", "operator": "match", "value": "kubeflow"},
        {"field": "ts_vector", "operator": "match", "value": "kubeflow"},
        {"field": "ts_vector", "operator": "match", "value": "kubeflow"},
    ],
    "sorting123": [{"field": "id", "direction": "desc"}],
}

example_4 = {
    "filters": [
        {"field": "id", "operator": "gt", "value": 1000},
        {"field": "pages", "operator": "is_null", "value": True},
    ]
}


def test_positive_standard_structure():
    assert map_request_to_filter(example_1, "test_model") == {
        "pagination": {"page_num": 1, "page_size": 50},
        "filters": [
            {
                "model": "test_model",
                "field": "ts_vector",
                "op": "match",
                "value": "kubeflow",
            }
        ],
        "sorting": [
            {"model": "test_model", "field": "id", "direction": "desc"}
        ],
    }


def test_positive_many_nested_structures():
    assert map_request_to_filter(example_2, "test_model") == {
        "pagination": {"page_num": 1, "page_size": 50},
        "filters": [
            {
                "model": "test_model",
                "field": "ts_vector",
                "op": "match",
                "value": "kubeflow",
            },
            {
                "model": "test_model",
                "field": "original_name",
                "op": "eq",
                "value": "epam",
            },
            {
                "model": "test_model",
                "field": "pages",
                "op": "gt",
                "value": 100,
            },
        ],
        "sorting": [
            {"model": "test_model", "field": "created", "direction": "desc"}
        ],
    }


def test_negative_invalid_keys():
    assert map_request_to_filter(example_3, "test_model") == {
        "pagination": {},
        "filters": [],
        "sorting": [],
    }


def test_positive_one_key():
    assert map_request_to_filter(example_4, "test_model") == {
        "pagination": {},
        "filters": [
            {"model": "test_model", "field": "id", "op": "gt", "value": 1000},
            {
                "model": "test_model",
                "field": "pages",
                "op": "is_null",
                "value": True,
            },
        ],
        "sorting": [],
    }
