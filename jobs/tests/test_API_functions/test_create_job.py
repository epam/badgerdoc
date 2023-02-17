import asyncio
import datetime
from unittest.mock import patch

import aiohttp.client_exceptions
import freezegun
import jobs.create_job_funcs as create_job_funcs
import jobs.schemas as schemas
import pytest


# ----------- Create Job Drafts ------------- #
def test_create_annotation_job_draft(testing_app, jw_token):
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
            "categories": ["category1", "category2"],
            "validation_type": schemas.ValidationType.hierarchical,
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
            "is_draft": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == schemas.Status.draft


def test_create_annotation_job_linked_taxonomy(testing_app, jw_token):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [(200, {})]
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
                "categories": [
                    "category1",
                    {
                        "category_id": "category2",
                        "taxonomy_id": "my_taxonomy_id",
                        "taxonomy_version": 1,
                    },
                ],
                "validation_type": schemas.ValidationType.hierarchical,
                "is_auto_distribution": False,
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == schemas.Status.draft
        assert response.json()["categories"] == ["category1", "category2"]


def test_create_annotation_job_without_deadline(testing_app):
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
            "categories": ["category1", "category2"],
            "validation_type": schemas.ValidationType.hierarchical,
            "is_auto_distribution": False,
            "is_draft": True,
        },
    )

    assert response.status_code == 200
    assert not response.json().get("deadline")


def test_create_extraction_job_draft(
    testing_app,
    separate_files_1_2_data_from_dataset_manager,
    pipeline_info_from_pipeline_manager,
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, pipeline_info_from_pipeline_manager),
            (200, separate_files_1_2_data_from_dataset_manager),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "test_extraction_job",
                "type": "ExtractionJob",
                "files": [1, 2],
                "datasets": [],
                "is_draft": True,
                "pipeline_name": "pipeline",
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "test_extraction_job"
        assert response.json()["status"] == schemas.Status.draft


def test_create_extraction_with_annotation_job_draft(
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
        assert response.json()["name"] == "MockExtractionWithAnnotationJob"
        assert response.json()["status"] == schemas.Status.draft


# ----------- Create Jobs ------------- #


def test_schedule_manual_job_valid_datasets(
    testing_app, mock_data_dataset11, mock_data_dataset22
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, mock_data_dataset11),
            (200, mock_data_dataset22),
            (200, {}),
            (200, {}),
        ]
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
                "categories": ["category1", "category2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "is_auto_distribution": False,
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": False,
            },
        )
        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["name"] == "MockAnnotationJob"


def test_schedule_manual_job_one_invalid_dataset(
    testing_app, mock_data_dataset11
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, mock_data_dataset11),
            (404, {"detail": "Dataset dataset121 does not exist!"}),
            (200, {}),
            (200, {}),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "MockAnnotationJob",
                "type": "AnnotationJob",
                "datasets": [1, 111],
                "files": [],
                "owners": ["owner1", "owner2"],
                "annotators": ["annotator1", "annotator2"],
                "validators": ["validator1", "validator2"],
                "categories": ["category1", "category2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "is_auto_distribution": False,
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
            },
        )
        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["name"] == "MockAnnotationJob"


def test_create_extraction_job_valid_files(
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
                "name": "test_extraction_job",
                "type": "ExtractionJob",
                "files": [1, 2],
                "datasets": [1, 2],
                "is_draft": False,
                "pipeline_name": "pipeline",
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "test_extraction_job"
        assert not response.json()["annotators"]
        assert not response.json()["validators"]
        assert not response.json()["owners"]


def test_create_extraction_job_with_output_bucket(
    testing_app,
    pipeline_info_from_pipeline_manager,
    separate_files_1_2_data_from_dataset_manager,
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, pipeline_info_from_pipeline_manager),
            (200, separate_files_1_2_data_from_dataset_manager),
            (200, [{"id": 426}]),
            (200, {}),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            headers={"tenant": "another_bucket"},
            json={
                "name": "test_extraction_job",
                "type": "ExtractionJob",
                "files": [1, 2],
                "datasets": [],
                "pipeline_name": "pipeline",
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "test_extraction_job"


def test_create_extraction_job_invalid_pipeline_name(
    testing_app, separate_files_1_2_data_from_dataset_manager
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            aiohttp.client_exceptions.ClientError(),
            (200, separate_files_1_2_data_from_dataset_manager),
            (200, [{"id": 426}]),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "test_extraction_job",
                "type": "ExtractionJob",
                "files": [1, 2],
                "datasets": [],
                "pipeline_name": "invalid_pipeline_name",
            },
        )

        assert response.status_code == 422
        assert response.json()["detail"].startswith(
            "Failed request to the Pipeline Manager"
        )


def test_create_extraction_with_annotation_job(
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
                "categories": ["category1", "category2"],
                "validation_type": schemas.ValidationType.hierarchical,
                "is_auto_distribution": False,
                "pipeline_name": "pipeline",
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": False,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == schemas.Status.pending


@pytest.mark.asyncio
async def test_get_all_datasets_and_files_data(
    mock_data_dataset11,
    mock_data_dataset22,
    separate_files_1_2_data_from_dataset_manager,
    jw_token,
):
    side_effect_ = [
        (200, mock_data_dataset11),
        (200, mock_data_dataset22),
        (200, separate_files_1_2_data_from_dataset_manager),
    ]
    with patch("jobs.utils.fetch", side_effect=side_effect_):
        mock_dataset_tags = [1, 2]
        mock_files_ids = [1, 2]
        current_tenant = "test"
        assert await create_job_funcs.get_all_datasets_and_files_data(
            mock_dataset_tags, mock_files_ids, current_tenant, jw_token
        ) == (
            [
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 1,
                    "last_modified": "2021-10-22T07:00:31.964897",
                    "original_name": "3.pdf",
                    "pages": 10,
                    "path": "files/1/1.pdf",
                    "size_in_bytes": 44900,
                    "status": "uploaded",
                },
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 2,
                    "last_modified": "2021-10-22T07:00:32.106530",
                    "original_name": "4.pdf",
                    "pages": 2,
                    "path": "files/2/2.pdf",
                    "size_in_bytes": 30111,
                    "status": "uploaded",
                },
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset22"],
                    "extension": ".pdf",
                    "id": 3,
                    "last_modified": "2021-10-22T07:00:32.239522",
                    "original_name": "33.pdf",
                    "pages": 6,
                    "path": "files/3/3.pdf",
                    "size_in_bytes": 917433,
                    "status": "uploaded",
                },
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset22"],
                    "extension": ".pdf",
                    "id": 4,
                    "last_modified": "2021-10-22T07:00:32.398579",
                    "original_name": "44.pdf",
                    "pages": 32,
                    "path": "files/4/4.pdf",
                    "size_in_bytes": 2680002,
                    "status": "uploaded",
                },
                {
                    "bucket": "tenant1",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 1,
                    "last_modified": "2021-11-19T12:26:18.815466",
                    "original_name": "3.pdf",
                    "pages": 10,
                    "path": "files/1/1.pdf",
                    "size_in_bytes": 44900,
                    "status": "uploaded",
                },
                {
                    "bucket": "tenant1",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 2,
                    "last_modified": "2021-11-19T12:26:18.959314",
                    "original_name": "4.pdf",
                    "pages": 2,
                    "path": "files/2/2.pdf",
                    "size_in_bytes": 30111,
                    "status": "uploaded",
                },
            ],
            [1, 2],
            [1, 2],
        )


def test_create_extraction_job_test_categories(
    testing_app,
    separate_files_1_2_data_from_dataset_manager,
    pipeline_info_from_pipeline_manager,
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, pipeline_info_from_pipeline_manager),
            (200, separate_files_1_2_data_from_dataset_manager),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "test_extraction_job",
                "type": "ExtractionJob",
                "files": [1, 2],
                "datasets": [],
                "is_draft": True,
                "pipeline_name": "pipeline",
            },
        )
        assert response.status_code == 200
        assert response.json()["categories"] == [
            "title",
            "header",
            "table",
            "figure",
            "footer",
            "not_chart",
            "text",
            "chart",
            "molecule",
        ]


def test_create_extraction_with_annotation_job_test_categories(
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
        assert sorted(response.json()["categories"]) == [
            "category1",
            "category2",
            "chart",
            "figure",
            "footer",
            "header",
            "molecule",
            "not_chart",
            "table",
            "text",
            "title",
        ]


def test_create_extraction_with_annotation_job_test_intersected_categories(
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
                "categories": ["text", "category2", "footer"],
                "is_auto_distribution": False,
                "pipeline_name": "pipeline",
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": True,
            },
        )
        assert response.status_code == 200
        assert sorted(response.json()["categories"]) == [
            "category2",
            "chart",
            "figure",
            "footer",
            "header",
            "molecule",
            "not_chart",
            "table",
            "text",
            "title",
        ]


def test_create_extraction_with_annotation_job_test_no_categories(
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
                # no categories set
                "is_auto_distribution": False,
                "pipeline_name": "pipeline",
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": True,
            },
        )
        assert response.status_code == 200
        assert sorted(response.json()["categories"]) == [
            "chart",
            "figure",
            "footer",
            "header",
            "molecule",
            "not_chart",
            "table",
            "text",
            "title",
        ]


@freezegun.freeze_time("2022-01-01")
def test_create_import_job(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockImportJob",
            "type": "ImportJob",
            "import_source": "s3bucket",
            "import_format": "jpg",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "import_format": "jpg",
        "id": 1,
        "creation_datetime": "2022-01-01T00:00:00",
        "name": "MockImportJob",
        "import_source": "s3bucket",
        "type": "ImportJob",
        "extensive_coverage": 1,
    }


def test_create_annotation_job_validation_only(
    testing_app, mock_data_dataset11, mock_data_dataset22
):
    with patch("jobs.utils.fetch", return_value=asyncio.Future()) as mock:
        mock.side_effect = [
            (200, mock_data_dataset11),
            (200, mock_data_dataset22),
            (200, {}),
            (200, {}),
        ]
        response = testing_app.post(
            "/jobs/create_job",
            json={
                "name": "MockAnnotationJob",
                "type": "AnnotationJob",
                "datasets": [1, 2],
                "files": [],
                "owners": ["owner1", "owner2"],
                "annotators": [],
                "validators": ["validator1", "validator2"],
                "categories": ["category1", "category2"],
                "validation_type": schemas.ValidationType.validation_only,
                "is_auto_distribution": False,
                "deadline": str(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1)
                ),
                "is_draft": False,
            },
        )
        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["validation_type"] == "validation only"
