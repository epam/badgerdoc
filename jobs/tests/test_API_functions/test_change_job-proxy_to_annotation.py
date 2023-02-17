import asyncio
from unittest.mock import patch

from tests.test_db import create_mock_annotation_job_in_db


def test_change_annotation_job_with_request_to_annotation(
    testing_app, testing_session, mock_AnnotationJobParams2
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [(200, {})]
        create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams2)
        response = testing_app.put(
            "/jobs/1",
            json={
                "annotators": ["annotator111", "annotator222"],
                "validators": ["validator111", "validator222"],
            },
        )
        assert response.status_code == 200
        mock.assert_awaited_once()
        assert mock.await_args.kwargs["body"] == (
            {
                "annotators": ["annotator111", "annotator222"],
                "validators": ["validator111", "validator222"],
            }
        )


def test_change_annotation_job_without_request_to_annotation(
    testing_app, testing_session, mock_AnnotationJobParams2
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams2)
        response = testing_app.put("/jobs/1", json={"status": "Finished"})
        assert response.status_code == 200
        assert response.json()["status"] == "Finished"
        # check there were no requests to "Annotation" microservice to update job
        mock.assert_not_awaited()


def test_change_annotation_job_with_partial_request_to_annotation(
    testing_app, testing_session, mock_AnnotationJobParams2
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [(200, {})]
        create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams2)
        response = testing_app.put(
            "/jobs/1",
            json={
                "annotators": ["annotator111", "annotator222"],
                "validators": ["validator111", "validator222"],
                "name": "new_name",
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "new_name"
        # register request to "Annotation" microservice to update job
        mock.assert_awaited_once()
        assert mock.await_args.kwargs["body"] == (
            {
                "annotators": ["annotator111", "annotator222"],
                "validators": ["validator111", "validator222"],
            }
        )
