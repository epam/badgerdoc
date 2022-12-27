from tests.test_db import (
    create_mock_annotation_job_in_db,
    create_mock_extraction_job_in_db,
)


def test_search_job_positive(testing_app, testing_session):
    create_mock_extraction_job_in_db(testing_session)
    response = testing_app.post(
        "/jobs/search",
        json={
            "pagination": {"page_num": 1, "page_size": 15},
            "filters": [
                {"field": "id", "operator": "is_not_null", "value": "string"}
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["data"][0]["name"] == "test_extraction_job_1"


def test_search_job_invalid_field(testing_app, testing_session):
    create_mock_extraction_job_in_db(testing_session)
    response = testing_app.post(
        "/jobs/search",
        json={
            "pagination": {"page_num": 1, "page_size": 15},
            "filters": [
                {
                    "field": "invalid field name",
                    "operator": "is_not_null",
                    "value": "string",
                }
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
    )
    assert response.status_code == 422
    response_message = response.json()['detail'][0]['msg']
    assert response_message.startswith("value is not a valid enumeration member")


def test_search_job_without_filters(
    testing_app, testing_session, mock_AnnotationJobParams
):
    create_mock_extraction_job_in_db(testing_session)
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    response = testing_app.post(
        "/jobs/search",
        json={
            "pagination": {"page_num": 1, "page_size": 15},
            "sorting": [{"field": "id", "direction": "asc"}],
        },
    )
    assert response.status_code == 200


def test_search_job_with_empty_request_body(
    testing_app, testing_session, mock_AnnotationJobParams
):
    create_mock_extraction_job_in_db(testing_session)
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    response = testing_app.post(
        "/jobs/search",
        json={},
    )
    assert response.status_code == 200


def test_search_job_has_pagination(
    testing_app, testing_session, mock_AnnotationJobParams
):
    for _ in range(25):
        create_mock_extraction_job_in_db(testing_session)
        create_mock_annotation_job_in_db(
            testing_session, mock_AnnotationJobParams
        )

    response1 = testing_app.post(
        "/jobs/search",
        json={
            "pagination": {"page_num": 1, "page_size": 15},
            "filters": [
                {"field": "id", "operator": "is_not_null", "value": "string"}
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
    )
    assert response1.status_code == 200
    assert response1.json()["pagination"] == {
        "has_more": False,
        "min_pages_left": 4,
        "page_num": 1,
        "page_size": 15,
        "total": 50,
    }

    response2 = testing_app.post(
        "/jobs/search",
        json={
            "pagination": {"page_num": 2, "page_size": 15},
            "filters": [
                {"field": "id", "operator": "is_not_null", "value": "string"}
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
    )
    assert response2.status_code == 200
    assert response2.json()["pagination"] == {
        "has_more": False,
        "min_pages_left": 4,
        "page_num": 2,
        "page_size": 15,
        "total": 50,
    }
