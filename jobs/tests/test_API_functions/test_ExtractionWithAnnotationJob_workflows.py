import asyncio
import datetime
from unittest.mock import patch

import pytest

import jobs.schemas as schemas


@pytest.mark.skip(reason="tests refactoring")
def test_change_extraction_job_to_extraction_with_annotation_job_and_run_it(
    testing_app,
    testing_session,
    separate_files_1_2_data_from_dataset_manager,
    pipeline_info_from_pipeline_manager,
    mock_data_dataset11,
    mock_data_dataset22,
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, pipeline_info_from_pipeline_manager),
            (200, mock_data_dataset11),
            (200, mock_data_dataset22),
            (200, separate_files_1_2_data_from_dataset_manager),
            (200, [{"id": 426}]),
            (200, {}),
            (200, {}),
            (200, {}),
        ]
        response1 = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "test_extraction_job",
                "type": "ExtractionJob",
                "files": [1, 2],
                "datasets": [1, 2],
                "is_draft": False,
                "pipeline_name": "pipeline",
            },
        )
        assert response1.status_code == 200
        assert response1.json()["status"] == schemas.Status.pending
        assert response1.json()["mode"] == schemas.JobMode.Automatic
        job_id = int(response1.json()["id"])

        # Changing Job Status to Finished - imitates
        # callback from pipelines service
        response2 = testing_app.put(
            f"/jobs/{job_id}", json={"status": "Finished"}
        )
        assert response2.status_code == 200
        assert response2.json()["status"] == schemas.Status.finished

        # Changing JobType to ExtractionWithAnnotationJob
        # and adding necessary fields

        response3 = testing_app.put(
            f"/jobs/{job_id}",
            json={
                "type": "ExtractionWithAnnotationJob",
                "is_auto_distribution": False,
                "owners": ["owner1", "owner2", "user_id"],
                "annotators": ["annotator1", "annotator2"],
                "validators": [],
                "validation_type": schemas.ValidationType.cross,
                "categories": ["category1", "category2"],
                "deadline": "2021-11-23T15:04:10.087Z",
            },
        )
        assert response3.status_code == 200
        assert (
            response3.json()["type"]
            == schemas.JobType.ExtractionWithAnnotationJob
        )
        assert (
            response3.json()["status"] == schemas.Status.ready_for_annotation
        )
        assert response3.json()["mode"] == schemas.JobMode.Manual

        # Running ExtractionWithAnnotationJob - only manual part
        response4 = testing_app.post("/start/1")
        assert response4.status_code == 200
        assert response4.json()["status"] == schemas.Status.pending
        assert response4.json()["mode"] == schemas.JobMode.Manual

        # Changing Job Status to Finished - imitates
        # callback from annotation service
        response5 = testing_app.put("/jobs/1", json={"status": "Finished"})
        assert response5.status_code == 200
        assert response5.json()["status"] == schemas.Status.finished


@pytest.mark.skip(reason="tests refactoring")
def test_create_extraction_with_annotation_job_and_run_it(
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
            (200, {}),
            (200, {}),
            (200, {}),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "MockExtractionWithAnnotationJob",
                "type": "ExtractionWithAnnotationJob",
                "datasets": [1, 2],
                "files": [1, 2],
                "owners": ["owner1", "owner2", "user_id"],
                "annotators": ["annotator1", "annotator2"],
                "validators": ["validator1", "validator2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "categories": ["category1", "category2"],
                "is_auto_distribution": False,
                "pipeline_name": "pipeline",
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": False,
            },
        )
        assert mock.await_count == 6
        assert response.status_code == 200
        assert response.json()["mode"] == schemas.JobMode.Automatic
        assert response.json()["status"] == schemas.Status.pending

        test_job_id = int(response.json()["id"])
        # Changing Job Status to Finished - imitates
        # callback from pipelines service
        response2 = testing_app.put(
            f"/jobs/{test_job_id}", json={"status": "Finished"}
        )
        assert response2.status_code == 200
        assert (
            response2.json()["status"] == schemas.Status.ready_for_annotation
        )
        assert response2.json()["mode"] == schemas.JobMode.Manual

        # Changing Job Status to In Progress - imitates
        # callback from annotation service
        response3 = testing_app.put(
            f"/jobs/{test_job_id}", json={"status": "In Progress"}
        )
        assert response3.status_code == 200
        assert response3.json()["status"] == schemas.Status.in_progress
        assert response3.json()["mode"] == schemas.JobMode.Manual

        # Then Manual Part executes from annotation service

        # Changing Job Status to Finished - imitates
        # callback from annotation service
        response5 = testing_app.put(
            f"/jobs/{test_job_id}", json={"status": "Finished"}
        )
        assert response5.status_code == 200
        assert response5.json()["status"] == schemas.Status.finished


@pytest.mark.skip(reason="tests refactoring")
def test_create_extraction_with_annotation_job_and_autostart_false(
    testing_app,
    mock_data_dataset11,
    mock_data_dataset22,
    separate_files_1_2_data_from_dataset_manager,
    pipeline_info_from_pipeline_manager,
):
    # Creating ExtractionWithAnnotationJob and running it
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, pipeline_info_from_pipeline_manager),
            (200, mock_data_dataset11),
            (200, mock_data_dataset22),
            (200, separate_files_1_2_data_from_dataset_manager),
            (200, [{"id": 426}]),
            (200, {}),
            (200, {}),
            (200, {}),
            (200, {}),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "MockExtractionWithAnnotationJob",
                "type": "ExtractionWithAnnotationJob",
                "datasets": [1, 2],
                "files": [1, 2],
                "owners": ["owner1", "owner2", "user_id"],
                "annotators": ["annotator1", "annotator2"],
                "validators": ["validator1", "validator2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "categories": ["category1", "category2"],
                "is_auto_distribution": False,
                "pipeline_name": "pipeline",
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": False,
                "start_manual_job_automatically": False,
            },
        )
        assert mock.await_count == 6
        assert response.status_code == 200
        assert response.json()["mode"] == schemas.JobMode.Automatic
        assert response.json()["status"] == schemas.Status.pending

        test_job_id = int(response.json()["id"])
        # Changing Job Status to Finished - imitates
        # callback from pipelines service
        response2 = testing_app.put(
            f"/jobs/{test_job_id}", json={"status": "Finished"}
        )
        assert response2.status_code == 200
        assert (
            response2.json()["status"] == schemas.Status.ready_for_annotation
        )
        assert response2.json()["mode"] == schemas.JobMode.Manual
