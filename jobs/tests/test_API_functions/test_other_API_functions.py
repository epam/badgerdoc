import asyncio
from unittest.mock import patch
import jobs.schemas as schemas
from tests.test_db import (
    create_mock_annotation_job_in_db,
    create_mock_extraction_job_in_db,
)


def test_get_all_jobs_endpoint(
    testing_app, testing_session, mock_AnnotationJobParams
):
    create_mock_extraction_job_in_db(testing_session)
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)

    response = testing_app.get("/jobs")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "test_extraction_job_1"
    assert response.json()[1]["name"] == "MockAnnotationJob"


def test_get_job_by_id_positive(
    testing_app, testing_session, mock_AnnotationJobParams
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [(200, "annotator_username1"), (200, "annotator_username2")]
        create_mock_extraction_job_in_db(testing_session)
        create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
        response = testing_app.get("/jobs/2")
        assert response.status_code == 200
        assert response.json()["name"] == "MockAnnotationJob"


def test_get_job_by_id_negative(
    testing_app, testing_session, mock_AnnotationJobParams
):
    create_mock_extraction_job_in_db(
        testing_session,
    )
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    response = testing_app.get("/jobs/3")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job with this id does not exist."


def test_delete_job_positive(
    testing_app, testing_session, mock_AnnotationJobParams
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [(200, {})]
        create_mock_extraction_job_in_db(testing_session)
        create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
        response = testing_app.delete(
            "/jobs/2",
        )
        assert response.status_code == 200
        assert response.json() == {"success": "Job with id=2 was deleted"}


def test_delete_job_invalid_job_id(
    testing_app, testing_session, mock_AnnotationJobParams
):
    create_mock_extraction_job_in_db(testing_session)
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    response = testing_app.delete(
        "/jobs/12345",
    )
    assert response.status_code == 404


def test_get_metadata(testing_app):
    response = testing_app.get("/metadata")
    assert response.status_code == 200
    assert list(response.json().keys()) == [
        schemas.JobType.__name__,
        schemas.Status.__name__,
        schemas.ValidationType.__name__,
    ]
    assert list(response.json().values())[0] == [
        member.value for member in schemas.JobType
    ]
