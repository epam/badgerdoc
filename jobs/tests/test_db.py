import pytest
from sqlalchemy.orm import Session

import jobs.db_service as db_service
import jobs.models as dbm
import jobs.schemas as schemas


@pytest.mark.skip(reason="tests refactoring")
def test_check_connection(testing_session):
    assert testing_session.query(dbm.CombinedJob).all() == []


all_files_data = [
    {
        "id": 3,
        "original_name": "33.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 917433,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 6,
        "last_modified": "2021-11-15T07:27:25.783934",
        "status": "uploaded",
        "path": "files/3/3.pdf",
        "datasets": ["dataset22"],
    },
    {
        "id": 4,
        "original_name": "44.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 2680002,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 32,
        "last_modified": "2021-11-15T07:27:25.936870",
        "status": "uploaded",
        "path": "files/4/4.pdf",
        "datasets": ["dataset22"],
    },
    {
        "id": 5,
        "original_name": "55.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 965981,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 20,
        "last_modified": "2021-11-15T07:27:26.183839",
        "status": "uploaded",
        "path": "files/5/5.pdf",
        "datasets": ["dataset22"],
    },
    {
        "id": 1,
        "original_name": "3.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 44900,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 10,
        "last_modified": "2021-11-15T07:27:25.508259",
        "status": "uploaded",
        "path": "files/1/1.pdf",
        "datasets": ["dataset11"],
    },
    {
        "id": 2,
        "original_name": "4.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 30111,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 2,
        "last_modified": "2021-11-15T07:27:25.659882",
        "status": "uploaded",
        "path": "files/2/2.pdf",
        "datasets": ["dataset11"],
    },
]


@pytest.mark.skip(reason="tests refactoring")
def test_create_extraction_job_in_db(testing_session):
    first_quantity_of_jobs = len(db_service.get_all_jobs(testing_session))
    assert db_service.create_extraction_job(
        db=testing_session,
        job_name="test_extraction_job_1",
        pipeline_id=1,
        valid_separate_files_ids=[1, 2],
        valid_dataset_ids=[1, 2],
        all_files_data=all_files_data,
        status=schemas.Status.pending,
        categories=["label"],
    )
    second_quantity_of_jobs = len(db_service.get_all_jobs(testing_session))
    assert second_quantity_of_jobs - first_quantity_of_jobs == 1


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotation_job_in_db(
    testing_session, mock_AnnotationJobParams
):
    first_quantity_of_jobs = len(db_service.get_all_jobs(testing_session))
    assert db_service.create_annotation_job(
        db=testing_session,
        annotation_job_input=mock_AnnotationJobParams,
        status=schemas.Status.pending,
    )
    second_quantity_of_jobs = len(db_service.get_all_jobs(testing_session))
    assert second_quantity_of_jobs - first_quantity_of_jobs == 1


def create_mock_extraction_job_in_db(testing_session):
    result = db_service.create_extraction_job(
        db=testing_session,
        job_name="test_extraction_job_1",
        pipeline_id=1,
        valid_separate_files_ids=[1, 2],
        valid_dataset_ids=[1, 2],
        all_files_data=all_files_data,
        status=schemas.Status.pending,
        categories=["label"],
        pipeline_engine="airflow",
        previous_jobs=[100],
        revisions=[],
    )
    return result


def create_mock_extraction_job_in_db_draft(testing_session):
    result = db_service.create_extraction_job(
        db=testing_session,
        job_name="test_extraction_job_1",
        pipeline_id=1,
        valid_separate_files_ids=[1, 2],
        valid_dataset_ids=[1, 2],
        all_files_data=all_files_data,
        status=schemas.Status.draft,
        categories=["label"],
    )
    return result


def create_mock_annotation_job_in_db(
    testing_session, mock_AnnotationJobParams
):
    result = db_service.create_annotation_job(
        db=testing_session,
        annotation_job_input=mock_AnnotationJobParams,
        status=schemas.Status.pending,
    )
    return result


@pytest.fixture
def create_mock_annotation_extraction_job_in_db(
    testing_session: Session,
    mock_extraction_annotation_job_params: schemas.ExtractionWithAnnotationJobParams,
):
    """Creates a mock Extraction and Annotation job in the database."""

    yield db_service.create_extraction_annotation_job(
        db=testing_session,
        extraction_annotation_job_input=mock_extraction_annotation_job_params,
        pipeline_id="1",
        pipeline_engine="airflow",
        valid_separate_files_ids=[1, 2],
        valid_dataset_ids=[1, 2],
        previous_jobs=[],
        all_files_data=all_files_data,
        categories=["cat1", "cat22"],
    )


@pytest.mark.skip(reason="tests refactoring")
def test_get_all_jobs_in_db(testing_session):
    create_mock_extraction_job_in_db(testing_session)
    result = db_service.get_all_jobs(testing_session)
    assert result
    assert isinstance(result, list)
    assert result[0]["name"] == "test_extraction_job_1"


@pytest.mark.skip(reason="tests refactoring")
def test_get_job_by_id(testing_session, mock_AnnotationJobParams):
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    test_id = 1
    result = db_service.get_job_in_db_by_id(db=testing_session, job_id=test_id)
    assert isinstance(result, dbm.CombinedJob)


@pytest.mark.skip(reason="tests refactoring")
def test_update_job_status_in_db(testing_session, mock_AnnotationJobParams):
    create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    job_for_test = db_service.get_job_in_db_by_id(testing_session, 1)
    new_status1 = schemas.Status.finished
    db_service.update_job_status(
        db=testing_session, job=job_for_test, new_status=new_status1
    )
    assert job_for_test.status == schemas.Status.finished
    new_status2 = schemas.Status.pending
    assert db_service.update_job_status(
        db=testing_session, job=job_for_test, new_status=new_status2
    )
    assert job_for_test.status == schemas.Status.pending


@pytest.mark.skip(reason="tests refactoring")
def test_delete_job(testing_session, mock_AnnotationJobParams):
    create_mock_extraction_job_in_db(testing_session)
    job_to_delete = create_mock_annotation_job_in_db(
        testing_session, mock_AnnotationJobParams
    )
    assert len(db_service.get_all_jobs(testing_session)) == 2
    db_service.delete_job(testing_session, job_to_delete)
    assert len(db_service.get_all_jobs(testing_session)) == 1


@pytest.mark.skip(reason="tests refactoring")
def test_create_ImportJob(testing_session):
    mockImportJobParams = schemas.ImportJobParams(
        name="MockImportJob",
        type="ImportJob",
        import_source="s3bucket_123",
        import_bucket="jpg",
    )

    new_import_job = db_service.create_import_job(
        testing_session, mockImportJobParams
    )
    assert new_import_job
    assert new_import_job.name == "MockImportJob"
    assert new_import_job.type == schemas.JobType.ImportJob
