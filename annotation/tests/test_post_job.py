from unittest.mock import Mock, patch

import pytest
import responses
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session

from annotation.annotations import row_to_dict
from annotation.jobs import get_job_attributes_for_post
from annotation.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
    ASSETS_URL,
)
from annotation.models import (
    Category,
    File,
    Job,
    ManualAnnotationTask,
    User,
    association_job_annotator,
)
from annotation.schemas import (
    CategoryTypeSchema,
    JobStatusEnumSchema,
    JobTypeEnumSchema,
    ValidationSchema,
)
from tests.consts import POST_JOBS_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app
from tests.test_post import check_files_distributed_pages

client = TestClient(app)

CATEGORIES = [Category(id="1", name="Test", type=CategoryTypeSchema.box)]

POST_JOB_ANNOTATORS = (
    User(user_id="ab13c974-4324-41c7-9291-0a3ae15855ca"),
    User(
        user_id="e776c316-bb75-4294-9565-032e4089ff40",
        default_load=10,
    ),
    User(user_id="b908ccf0-6eab-4b8e-afb7-913372ddf4e5"),
    User(user_id="00d37dc4-b7da-45e5-bcb5-c9b82965351c"),
)
POST_JOB_NEW_USER = User(user_id="11d37dc4-b7da-45e5-bcb5-c9b82965352c")
POST_JOB_NEW_FILE_ID = 1
POST_JOB_NEW_DATASET_ID = 1
POST_JOB_EXISTING_FILE_ID = 2
POST_JOB_EXISTING_JOB_ID = 2
POST_JOB_EXISTING_FILE = File(
    file_id=POST_JOB_EXISTING_FILE_ID,
    tenant=TEST_TENANT,
    job_id=POST_JOB_EXISTING_JOB_ID,
    pages_number=10,
)
POST_JOB_EXISTING_JOB = {
    "job_id": POST_JOB_EXISTING_JOB_ID,
    "callback_url": "http://www.test.com/test1",
    "annotators": [POST_JOB_ANNOTATORS[0]],
    "validation_type": ValidationSchema.cross,
    "files": [POST_JOB_EXISTING_FILE],
    "is_auto_distribution": False,
    "categories": CATEGORIES,
    "deadline": None,
    "tenant": TEST_TENANT,
}
POST_JOB_NEW_JOBS = (
    {
        "job_id": POST_JOB_EXISTING_JOB_ID,
        "job": {
            "callback_url": "http://www.test.com/test2",
            "annotators": [
                POST_JOB_ANNOTATORS[0].user_id,
                POST_JOB_ANNOTATORS[1].user_id,
            ],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [POST_JOB_NEW_FILE_ID],
            "datasets": [],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": None,
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 3,
        "job": {
            "callback_url": "http://www.test.com/test3",
            "annotators": [str(user.user_id) for user in POST_JOB_ANNOTATORS],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [POST_JOB_NEW_FILE_ID],
            "datasets": [],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 4,
        "job": {
            "callback_url": "test/test4",
            "annotators": [str(user.user_id) for user in POST_JOB_ANNOTATORS],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [POST_JOB_NEW_FILE_ID],
            "datasets": [],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": None,
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 5,
        "job": {
            "callback_url": "test/test5",
            "annotators": [str(user.user_id) for user in POST_JOB_ANNOTATORS],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 6,
        "job": {
            "callback_url": "test/test5",
            "name": "AnnotationJob1",
            "annotators": [POST_JOB_ANNOTATORS[1].user_id],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.hierarchical,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 7,
        "job": {
            "callback_url": "test/test5",
            "annotators": [POST_JOB_ANNOTATORS[1].user_id],
            "validators": [POST_JOB_ANNOTATORS[1].user_id],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 8,
        "job": {
            "callback_url": "test/test5",
            "annotators": [POST_JOB_NEW_USER.user_id],
            "validators": [POST_JOB_NEW_USER.user_id],
            "owners": [POST_JOB_NEW_USER.user_id],
            "validation_type": ValidationSchema.hierarchical,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 9,
        "job": {
            "callback_url": "test/test5",
            "annotators": [POST_JOB_ANNOTATORS[1].user_id],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 10,
        "job": {
            "callback_url": "test/test5",
            "annotators": [POST_JOB_ANNOTATORS[1].user_id],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.validation_only,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 11,
        "job": {
            "callback_url": "test/test5",
            "annotators": [],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.validation_only,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
    },
    {
        "job_id": 12,
        "job": {
            "callback_url": "test/test_extraction",
            "name": "ExtractionJob1",
            "annotators": [],
            "validators": [],
            "owners": [POST_JOB_NEW_USER.user_id],
            "files": [POST_JOB_NEW_FILE_ID],
            "datasets": [],
            "is_auto_distribution": True,
            "categories": [CATEGORIES[0].id],
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.ExtractionJob,
        },
    },
    {
        "job_id": 13,
        "job": {
            "callback_url": "test/test_extraction",
            "annotators": [],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.validation_only,
            "files": [],
            "datasets": [],
            "is_auto_distribution": False,
            "categories": [CATEGORIES[0].id],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.ExtractionJob,
        },
    },
    {
        "job_id": 14,
        "job": {
            "callback_url": "test/test_extraction",
            "annotators": [],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.validation_only,
            "files": [],
            "datasets": [POST_JOB_NEW_DATASET_ID],
            "is_auto_distribution": False,
            "categories": [],
            "deadline": "2021-12-12T01:01:01",
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.ExtractionJob,
        },
    },
    {
        "job_id": 15,
        "job": {
            "callback_url": "test/test_extraction",
            "annotators": [],
            "validators": [],
            "owners": [POST_JOB_NEW_USER.user_id],
            "files": [POST_JOB_NEW_FILE_ID],
            "datasets": [],
            "is_auto_distribution": True,
            "categories": [CATEGORIES[0].id],
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.ExtractionJob,
        },
    },
    {  # Import job with no files, datasets or categories provided
        "job_id": 16,
        "job": {
            "callback_url": "http://www.test.com/test2",
            "name": "ImportJob1",
            "annotators": [],
            "validators": [],
            "owners": [POST_JOB_NEW_USER.user_id],
            "files": [],
            "datasets": [],
            "is_auto_distribution": False,
            "categories": [],
            "deadline": None,
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.ImportJob,
        },
    },
)
DATASET_MANAGER_FILE_RESPONSE = {
    "pagination": {
        "page_num": 1,
        "page_size": 15,
        "min_pages_left": 1,
        "total": 1,
        "has_more": False,
    },
    "data": [
        {
            "id": f"{POST_JOB_NEW_FILE_ID}",
            "original_name": "some.pdf",
            "bucket": "test",
            "size_in_bytes": 165887,
            "extension": ".pdf",
            "content_type": "image/png",
            "pages": 10,
            "last_modified": "2021-10-24T01:11:11",
            "status": "uploaded",
            "path": f"files/{POST_JOB_NEW_FILE_ID}/{POST_JOB_NEW_FILE_ID}.pdf",
            "datasets": [],
        }
    ],
}
DATASET_MANAGER_DATASET_RESPONSE = [
    {
        "id": f"{POST_JOB_NEW_FILE_ID}",
        "original_name": "some.pdf",
        "bucket": "test",
        "size_in_bytes": 165887,
        "extension": ".pdf",
        "content_type": "image/png",
        "pages": 10,
        "last_modified": "2021-10-24T01:11:11",
        "status": "uploading",
        "path": f"files/{POST_JOB_NEW_FILE_ID}/{POST_JOB_NEW_FILE_ID}.pdf",
        "datasets": [1],
    }
]


@pytest.mark.integration
@patch.object(Session, "query")
def test_post_job_connection_exception(Session, prepare_db_for_post_job):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.post(
        f"{POST_JOBS_PATH}/{POST_JOB_NEW_JOBS[0]['job_id']}",
        json=POST_JOB_NEW_JOBS[0]["job"],
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: connection error " in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_info", "expected_response_code", "expected_response"],
    [
        (POST_JOB_NEW_JOBS[0], 400, "The job already exists."),
        (POST_JOB_NEW_JOBS[1], 201, None),
        (POST_JOB_NEW_JOBS[2], 201, None),
        (POST_JOB_NEW_JOBS[3], 201, None),
        (
            POST_JOB_NEW_JOBS[4],
            422,
            (
                "If the validation type is hierarchical, annotators field "
                "and validators field should not be empty at the same "
            ),
        ),
        (
            POST_JOB_NEW_JOBS[5],
            422,
            (
                "cross validation, annotators field should have min 2 "
                "annotators and the validators field should be empty."
            ),
        ),
        (POST_JOB_NEW_JOBS[6], 201, None),
        (
            POST_JOB_NEW_JOBS[7],
            422,
            (
                "cross validation, annotators field should have min 2 "
                "annotators and the validators field should be empty."
            ),
        ),
        (
            POST_JOB_NEW_JOBS[8],
            422,
            (
                "validation type is validation_only, annotators field should "
                "be empty and validators field should not be empty."
            ),
        ),
        (
            POST_JOB_NEW_JOBS[9],
            422,
            (
                "validation type is validation_only, annotators field should "
                "be empty and validators field should not be empty."
            ),
        ),
        (
            POST_JOB_NEW_JOBS[11],
            422,
            (
                "Fields files and datasets should not be empty "
                "at the same time."
            ),
        ),  # even in ExtractionJob must be either files or datasets
    ],
)
@responses.activate
def test_post_job(
    prepare_db_for_post_job,
    job_info,
    expected_response_code,
    expected_response,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=DATASET_MANAGER_FILE_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    responses.add(
        responses.GET,
        f"{ASSETS_URL}/{POST_JOB_NEW_DATASET_ID}/files",
        json=DATASET_MANAGER_DATASET_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{job_info['job_id']}",
        json=job_info["job"],
        headers=TEST_HEADERS,
    )
    assert response.status_code == expected_response_code
    if response.status_code == 422:
        assert expected_response in response.json()["detail"][0]["msg"]
        return
    if response.status_code == 400:
        assert expected_response in response.json()["detail"]
        return
    assert response.json() == expected_response
    assert prepare_db_for_post_job.query(Job).get(job_info["job_id"])
    assert prepare_db_for_post_job.query(File).get(
        (
            (
                POST_JOB_NEW_FILE_ID
                if expected_response_code == 201
                else POST_JOB_EXISTING_FILE_ID
            ),
            job_info["job_id"],
        )
    )
    assert (
        prepare_db_for_post_job.query(association_job_annotator)
        .join(Job)
        .join(User)
        .filter(Job.job_id == job_info["job_id"])
        .all()
    )


@pytest.mark.integration
@responses.activate
def test_post_job_with_extensive_coverage_should_work(
    prepare_db_for_post_job, prepare_categories_with_tree
):
    new_job_id = 6
    session = prepare_db_for_post_job
    users = [
        POST_JOB_ANNOTATORS[1].user_id,
        POST_JOB_ANNOTATORS[2].user_id,
        POST_JOB_ANNOTATORS[3].user_id,
    ]
    validators = [POST_JOB_ANNOTATORS[3].user_id]
    requests_data = {
        "callback_url": "test6",
        "name": "AnnotationJob1",
        "annotators": users,
        "validators": validators,
        "owners": [],
        "validation_type": ValidationSchema.extensive_coverage,
        "extensive_coverage": 2,
        "files": [POST_JOB_NEW_FILE_ID],
        "datasets": [],
        "is_auto_distribution": True,
        "categories": ["13"],
        "deadline": "2021-12-12T01:01:01",
        "job_type": JobTypeEnumSchema.AnnotationJob,
    }
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=DATASET_MANAGER_FILE_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{new_job_id}",
        json=requests_data,
        headers=TEST_HEADERS,
    )
    assert response
    assert response.status_code == 201
    created_job_row = session.query(Job).get(new_job_id)
    assert created_job_row
    saved_job = row_to_dict(created_job_row)
    assert saved_job["is_auto_distribution"]
    assert session.query(File).get(
        (
            POST_JOB_NEW_FILE_ID,
            new_job_id,
        )
    )
    assert len(
        session.query(association_job_annotator)
        .join(Job)
        .join(User)
        .filter(Job.job_id == new_job_id)
        .all()
    ) == len(users)
    assert (
        len(
            session.query(ManualAnnotationTask)
            .filter(ManualAnnotationTask.job_id == new_job_id)
            .all()
        )
        == 3  # 2 annotation tasks and 1 validation
    )
    assert saved_job.pop("name") == "AnnotationJob1"
    assert saved_job.pop("job_type") == JobTypeEnumSchema.AnnotationJob
    check_files_distributed_pages(prepare_db_for_post_job, new_job_id)


@pytest.mark.integration
@responses.activate
def test_post_job_auto_distribution(prepare_db_for_post_job):
    new_job_id = 14
    session = prepare_db_for_post_job
    users = [
        POST_JOB_ANNOTATORS[1].user_id,
        POST_JOB_ANNOTATORS[2].user_id,
        POST_JOB_ANNOTATORS[3].user_id,
    ]
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=DATASET_MANAGER_FILE_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{new_job_id}",
        json={
            "callback_url": "test6",
            "name": f"AnnotationJob_{new_job_id}",
            "annotators": users,
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [POST_JOB_NEW_FILE_ID],
            "datasets": [],
            "is_auto_distribution": True,
            "categories": ["1"],
            "deadline": "2021-12-12T01:01:01",
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
        headers=TEST_HEADERS,
    )
    assert response
    assert response.status_code == 201
    new_job = session.query(Job).get(new_job_id)
    assert new_job
    saved_job = row_to_dict(session.query(Job).get(new_job_id))
    assert saved_job["is_auto_distribution"]
    assert session.query(File).get(
        (
            POST_JOB_NEW_FILE_ID,
            new_job_id,
        )
    )
    assert len(
        session.query(association_job_annotator)
        .join(Job)
        .join(User)
        .filter(Job.job_id == new_job_id)
        .all()
    ) == len(users)
    assert (
        len(
            session.query(ManualAnnotationTask)
            .filter(ManualAnnotationTask.job_id == new_job_id)
            .all()
        )
        == 2
    )
    assert saved_job.pop("name") == f"AnnotationJob_{new_job_id}"
    assert saved_job.pop("job_type") == JobTypeEnumSchema.AnnotationJob
    check_files_distributed_pages(prepare_db_for_post_job, new_job_id)


@pytest.mark.integration
@patch.object(Session, "bulk_insert_mappings")
@responses.activate
def test_post_job_auto_distribution_exc(Session, prepare_db_for_post_job):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    new_job_id = 7
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=DATASET_MANAGER_FILE_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{new_job_id}",
        json={
            "callback_url": "test6",
            "annotators": [str(user.user_id) for user in POST_JOB_ANNOTATORS],
            "validators": [],
            "owners": [],
            "validation_type": ValidationSchema.cross,
            "files": [POST_JOB_NEW_FILE_ID],
            "datasets": [],
            "is_auto_distribution": True,
            "categories": [1],
            "deadline": None,
            "job_type": JobTypeEnumSchema.AnnotationJob,
        },
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: connection error " in response.text
    assert not prepare_db_for_post_job.query(Job).get(new_job_id)
    assert not prepare_db_for_post_job.query(File).get(
        (
            POST_JOB_NEW_FILE_ID,
            new_job_id,
        )
    )
    assert not (
        prepare_db_for_post_job.query(association_job_annotator)
        .join(Job)
        .join(User)
        .filter(Job.job_id == new_job_id)
        .all()
    )
    assert not (
        prepare_db_for_post_job.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.job_id == new_job_id)
        .all()
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ["attribute_filter", "expected_result"],
    [
        ((Job,), POST_JOB_EXISTING_JOB["job_id"]),
        (
            (Job.callback_url, Job.tenant),
            (
                POST_JOB_EXISTING_JOB["callback_url"],
                POST_JOB_EXISTING_JOB["tenant"],
            ),
        ),
        ((Job.job_id,), (POST_JOB_EXISTING_JOB["job_id"],)),
    ],
)
def test_get_job_attributes_for_post(
    prepare_db_for_post_job, attribute_filter, expected_result
):
    db_job_info = get_job_attributes_for_post(
        prepare_db_for_post_job,
        POST_JOB_EXISTING_JOB["job_id"],
        TEST_TENANT,
        attribute_filter,
    )
    if isinstance(attribute_filter[0], DeclarativeMeta):
        assert isinstance(db_job_info, Job)
        assert db_job_info.job_id == expected_result
    else:
        assert db_job_info == expected_result


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_info", "expected_name"],
    [(POST_JOB_NEW_JOBS[10], "ExtractionJob1"), (POST_JOB_NEW_JOBS[13], None)],
)
@responses.activate
def test_post_extraction_job_saved(
    prepare_db_for_post_job, job_info, expected_name
):
    """Tests that new ExtractionJob with valid user type fields will be
    created in db in default 'pending' status  and that values for
    not-provided optional fields 'validation_type', 'deadline', 'name' are
    generated appropriately.
    """
    expected_response_code = 201
    session = prepare_db_for_post_job
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=DATASET_MANAGER_FILE_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        f"{POST_JOBS_PATH}/{job_info['job_id']}",
        json=job_info["job"],
        headers=TEST_HEADERS,
    )
    assert response.status_code == expected_response_code
    saved_job = row_to_dict(session.query(Job).get(job_info["job_id"]))
    assert not saved_job.get("deadline")
    assert saved_job.get("validation_type") == ValidationSchema.cross
    assert saved_job.get("status") == JobStatusEnumSchema.pending
    assert saved_job.get("job_id") == job_info["job_id"]
    assert saved_job.get("name") == expected_name
    assert saved_job.get("job_type") == JobTypeEnumSchema.ExtractionJob


@pytest.mark.integration
def test_post_import_job_saved(prepare_db_for_post_job):
    """Tests that new ImportJob with no users, no files or datasets provided
    will be created in db with correct values for all required fields"""
    job_info = POST_JOB_NEW_JOBS[14]
    expected_response_code = 201
    session = prepare_db_for_post_job
    response = client.post(
        f"{POST_JOBS_PATH}/{job_info['job_id']}",
        json=job_info["job"],
        headers=TEST_HEADERS,
    )
    assert response.status_code == expected_response_code
    saved_job = row_to_dict(session.query(Job).get(job_info["job_id"]))
    assert (
        not session.query(File).filter(File.job_id == job_info["job_id"]).all()
    )
    assert not saved_job.get("categories")
    assert not saved_job.get("deadline")
    assert saved_job.get("validation_type") == ValidationSchema.cross
    assert saved_job.get("job_type") == JobTypeEnumSchema.ImportJob
