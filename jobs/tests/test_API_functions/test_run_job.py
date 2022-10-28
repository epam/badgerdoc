import asyncio
import datetime
from unittest.mock import patch

import aiohttp.client_exceptions
import pytest
from requests import HTTPError

import jobs.schemas as schemas


def test_run_not_a_draft(testing_app):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, {}),
        ]
        testing_app.post(
            "/jobs/create_job",
            json={
                "name": "MockAnnotationJob",
                "type": "AnnotationJob",
                "datasets": [1, 2],
                "files": [],
                "owners": ["owner1", "owner2"],
                "annotators": ["annotator1", "annotator2"],
                "validators": ["validator1", "validator2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "categories": ["category1", "category2"],
                "is_auto_distribution": False,
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": False,
            },
        )
        response2 = testing_app.post("/start/1")
        assert response2.status_code == 406
        assert response2.json() == {
            "detail": "You can run only Job with a status 'Draft' or "
            "ExtractionWithAnnotationJob with finished Automatic part"
        }


def test_run_draft_annotation_job(testing_app):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, {}),
        ]
        testing_app.post(
            "/jobs/create_job",
            json={
                "name": "MockAnnotationJob",
                "type": "AnnotationJob",
                "datasets": [1, 2],
                "files": [],
                "owners": ["owner1", "owner2"],
                "annotators": ["annotator1", "annotator2"],
                "validators": ["validator1", "validator2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "categories": ["category1", "category2"],
                "is_auto_distribution": False,
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": True,
            },
        )
        response2 = testing_app.post("/start/1")
        assert response2.json()["status"] == schemas.Status.pending


def test_run_extraction_job(
    testing_app,
    mock_data_dataset11,
    mock_data_dataset22,
    separate_files_1_2_data_from_dataset_manager,
    pipeline_info_from_pipeline_manager,
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, pipeline_info_from_pipeline_manager),
            (200, mock_data_dataset11),
            (200, mock_data_dataset22),
            (200, separate_files_1_2_data_from_dataset_manager),
            (200, [{"id": 426}]),
        ]
        response1 = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "test_extraction_job",
                "type": "ExtractionJob",
                "files": [1, 2],
                "datasets": [1, 2],
                "is_draft": True,
                "pipeline_name": "pipeline",
            },
        )
        assert response1.status_code == 200
        assert response1.json()["status"] == schemas.Status.draft

        response2 = testing_app.post("/start/1")
        assert response2.status_code == 200
        assert response2.json()["status"] == schemas.Status.pending


def test_run_extraction_with_annotation_job(
    testing_app,
    mock_data_dataset11,
    mock_data_dataset22,
    separate_files_1_2_data_from_dataset_manager,
    pipeline_info_from_pipeline_manager,
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, pipeline_info_from_pipeline_manager),
            (200, mock_data_dataset11),
            (200, mock_data_dataset22),
            (200, separate_files_1_2_data_from_dataset_manager),
            (200, [{"id": 426}]),
            (200, {}),
        ]

        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "MockExtractionWithAnnotationJob",
                "type": "ExtractionWithAnnotationJob",
                "datasets": [1, 2],
                "files": [1, 2],
                "owners": ["owner1", "owner2"],
                "annotators": ["annotator1", "annotator2"],
                "validators": ["validator1", "validator2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "categories": ["category1", "category2"],
                "is_auto_distribution": False,
                "pipeline_name": "pipeline",
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == schemas.Status.draft

        response2 = testing_app.post("/start/1")
        assert response2.status_code == 200
        assert response2.json()["status"] == schemas.Status.pending


def test_run_annotation_job_but_server_is_down(testing_app):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [aiohttp.client_exceptions.ClientError()]
        with pytest.raises(HTTPError) as e_info:
            response = testing_app.post(
                "/jobs/create_job",
                json={
                    "name": "MockAnnotationJob",
                    "type": "AnnotationJob",
                    "datasets": [1, 2],
                    "files": [],
                    "owners": ["owner1", "owner2"],
                    "annotators": ["annotator1", "annotator2"],
                    "validators": ["validator1", "validator2"],
                    "validation_type": schemas.ValidationType.hierarchical,
                    "categories": ["category1", "category2"],
                    "is_auto_distribution": False,
                    "deadline": str(
                        datetime.datetime.utcnow() + datetime.timedelta(days=1)
                    ),
                    "is_draft": False,
                },
            )
            response.raise_for_status()
        assert e_info.value.response.status_code == 422
