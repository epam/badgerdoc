import asyncio
from unittest.mock import patch

import pytest
from tests.test_db import (create_mock_annotation_job_in_db,
                           create_mock_extraction_job_in_db)

import jobs.schemas as schemas


def test_change_job_status_with_validation_correct_jwt_provided(
    testing_app,
    testing_session,
    mock_AnnotationJobParams,
):

    create_mock_extraction_job_in_db(testing_session)
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    response2 = testing_app.put("/jobs/2", json={"status": "Finished"})
    assert response2.status_code == 200
    assert response2.json()["status"] == schemas.Status.finished


def test_change_job_status_correct_jwt_provided_and_incorrect_job_id(
    testing_app,
    testing_session,
    mock_AnnotationJobParams,
):

    create_mock_extraction_job_in_db(testing_session)
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    response2 = testing_app.put(
        "/jobs/333",
        json={"status": "Finished"},
    )
    assert response2.status_code == 404
    assert response2.json() == {"detail": "Job with this id does not exist."}


@pytest.mark.skip(
    reason="Check for job owner is temporarily disabled for development purposes"
)
def test_change_job_status_with_validation_incorrect_job_owner(
    testing_app,
    testing_session,
    mock_AnnotationJobParams2,
):

    create_mock_extraction_job_in_db(testing_session)
    create_mock_annotation_job_in_db(
        testing_session, mock_AnnotationJobParams2
    )
    response2 = testing_app.put(
        "/jobs/2",
        json={"status": "Finished"},
    )
    assert response2.status_code == 403
    assert response2.json() == {
        "detail": "Access denied. This user is not allowed to change the job"
    }


def test_change_job_pipeline_id(
    testing_app, testing_session, mock_AnnotationJobParams
):
    create_mock_extraction_job_in_db(testing_session)
    response = testing_app.put("/jobs/1", json={"pipeline_id": 555})
    assert response.status_code == 200
    assert response.json()["pipeline_id"] == str(555)


def test_change_job_linked_taxonomy(
    testing_app, testing_session, mock_AnnotationJobParams
):
    create_mock_extraction_job_in_db(testing_session)
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [(204, {}), (200, {})]
        response = testing_app.put(
            "/jobs/1",
            json={
                "categories": [
                    {
                        "category_id": "category2",
                        "taxonomy_id": "my_taxonomy_id",
                        "taxonomy_version": 1,
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json()["categories"] == ["category2"]
