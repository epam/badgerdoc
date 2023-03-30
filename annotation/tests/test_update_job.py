import os
from collections import Counter
from unittest.mock import Mock, patch

import responses
from fastapi.testclient import TestClient
from pytest import mark
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError

from annotation.annotations import row_to_dict
from annotation.models import (
    Category,
    File,
    Job,
    ManualAnnotationTask,
    User,
    association_job_annotator,
    association_job_category,
    association_job_owner,
    association_job_validator,
)
from annotation.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    JobTypeEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.consts import POST_JOBS_PATH
from tests.override_app_dependency import (
    TEST_HEADERS,
    TEST_TENANT,
    TEST_TOKEN,
    app,
)

JOBS_SEARCH_URL = os.environ.get("JOBS_SEARCH_URL")

client = TestClient(app)

OTHER_TENANT = "other"

USER_IDS = (
    "0c4963ad-200b-491e-925a-054814ebc721",  # annotator
    "0c4963ad-200b-491e-925a-054814ebc722",  # validator (annotator for cross)
    "0c4963ad-200b-491e-925a-054814ebc723",  # owner
    "0c4963ad-200b-491e-925a-054814ebc724",  # existing user with no jobs
)
UPDATE_NEW_USER_ID = "0c4963ad-200b-491e-925a-054814ebc725"
UPDATE_JOB_USERS = [
    User(user_id=USER_IDS[0]),  # annotator
    User(user_id=USER_IDS[1]),  # validator
    User(user_id=USER_IDS[2]),  # owner
]
UPDATE_USER_NO_JOBS = User(user_id=USER_IDS[3])


CATEGORIES_IDS = ("1", "2", "3")
UPDATE_JOB_CATEGORIES = [
    Category(
        id=CATEGORIES_IDS[0],
        name="Test1",
        tenant=TEST_TENANT,
        type=CategoryTypeSchema.box,
    ),
    Category(
        id=CATEGORIES_IDS[1],
        name="Test2",
        type=CategoryTypeSchema.box,
    ),  # common category
    Category(
        id=CATEGORIES_IDS[2],
        name="Test3",
        tenant=OTHER_TENANT,
        type=CategoryTypeSchema.box,
    ),
]
UPDATE_NOT_EXIST_CATEGORY_ID = "4"

UPDATE_JOB_IDS = (1, 2, 3, 4, 5, 6, 7, 8)
UPDATE_JOBS = (
    Job(
        job_id=UPDATE_JOB_IDS[0],  # cross validation job
        name="JobName1",
        callback_url="http://www.test.com/test1",
        annotators=UPDATE_JOB_USERS[:2],
        validators=[],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=[UPDATE_JOB_CATEGORIES[0]],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=UPDATE_JOB_IDS[1],  # hierarchical validation job
        name="JobName2",
        callback_url="http://www.test.com/test2",
        annotators=[UPDATE_JOB_USERS[0]],
        validators=[UPDATE_JOB_USERS[1]],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.hierarchical,
        is_auto_distribution=False,
        categories=[UPDATE_JOB_CATEGORIES[0]],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=UPDATE_JOB_IDS[2],  # other job for ForeignKey constraints cases
        callback_url="http://www.test.com/test3",
        annotators=[UPDATE_JOB_USERS[0]],
        validators=[UPDATE_JOB_USERS[1]],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.hierarchical,
        is_auto_distribution=False,
        categories=[UPDATE_JOB_CATEGORIES[0]],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=UPDATE_JOB_IDS[3],  # other tenant's job
        callback_url="http://www.test.com/test3",
        annotators=[UPDATE_JOB_USERS[0]],
        validators=[UPDATE_JOB_USERS[1]],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.hierarchical,
        is_auto_distribution=False,
        categories=[UPDATE_JOB_CATEGORIES[0]],
        deadline="2022-10-19T01:01:01",
        tenant=OTHER_TENANT,
    ),
    Job(
        job_id=UPDATE_JOB_IDS[4],  # validation only job
        callback_url="http://www.test.com/test2",
        annotators=[UPDATE_JOB_USERS[0]],
        validators=[UPDATE_JOB_USERS[1]],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.validation_only,
        is_auto_distribution=False,
        categories=[UPDATE_JOB_CATEGORIES[0]],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=UPDATE_JOB_IDS[5],  # already started job
        callback_url="http://www.test.com/test2",
        annotators=[UPDATE_JOB_USERS[0]],
        validators=[UPDATE_JOB_USERS[1]],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.hierarchical,
        is_auto_distribution=False,
        categories=[UPDATE_JOB_CATEGORIES[0]],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
        status=JobStatusEnumSchema.in_progress,
    ),
    Job(
        job_id=UPDATE_JOB_IDS[6],  # ExtractionJob
        callback_url="http://www.test.com/test2",
        annotators=[],
        validators=[],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.validation_only,
        is_auto_distribution=False,
        categories=[UPDATE_JOB_CATEGORIES[0]],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=UPDATE_JOB_IDS[7],  # ImportJob
        callback_url="http://www.test.com/test2",
        annotators=[],
        validators=[],
        owners=[UPDATE_JOB_USERS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=[],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
        job_type=JobTypeEnumSchema.ImportJob,
        name="Some Job",
    ),
)
UPDATE_WRONG_JOB_ID = 9

UPDATE_FILE_IDS = (1, 2, 3, 4)
UPDATE_JOB_FILES = [
    File(
        file_id=UPDATE_FILE_IDS[0],  # file related to the test job
        tenant=TEST_TENANT,
        job_id=UPDATE_JOBS[0].job_id,
        pages_number=1,
        distributed_annotating_pages=[],
        annotated_pages=[],
        distributed_validating_pages=[],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=UPDATE_FILE_IDS[1],  # file related to the other job
        tenant=TEST_TENANT,
        job_id=UPDATE_JOBS[2].job_id,
        pages_number=2,
        distributed_annotating_pages=[],
        annotated_pages=[],
        distributed_validating_pages=[],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=UPDATE_FILE_IDS[2],  # file related to started job
        tenant=TEST_TENANT,
        job_id=UPDATE_JOBS[5].job_id,
        pages_number=2,
        distributed_annotating_pages=[],
        annotated_pages=[],
        distributed_validating_pages=[],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),
]

UPDATE_JOB_FILES_FROM_ASSETS = [
    {
        "file_id": UPDATE_FILE_IDS[0],  # same file_id other pages
        "pages_number": 5,
    },
    {
        "file_id": UPDATE_FILE_IDS[1],  # same file_id with other job
        "pages_number": 2,
    },
    {
        "file_id": 3,  # new file_id
        "pages_number": 10,
    },
    {"file_id": UPDATE_FILE_IDS[2], "pages_number": 2},
]

ASSOCIATION_TABLES = {
    "annotators": association_job_annotator,
    "validators": association_job_validator,
    "owners": association_job_owner,
}


@mark.integration
@patch("annotation.jobs.resources.get_job", side_effect=SQLAlchemyError)
def test_update_job_connection_exception(prepare_db_for_update_job):
    """Tests error handling for SQLAlchemy errors."""
    response = client.patch(
        f"{POST_JOBS_PATH}/{UPDATE_JOB_IDS[0]}",
        json={"deadline": "2022-10-19T01:01:01"},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: connection error " in response.text


@mark.integration
@mark.parametrize(
    ["field", "new_value"],
    [
        ("callback_url", "http://www.test.com/new_url"),
        ("deadline", "2022-10-19 01:01:02"),
        ("name", "JobName1"),
    ],
)
def test_update_deadline_url_name(field, new_value, prepare_db_for_update_job):
    """Tests updating of fields without additional business logic involved."""
    session = prepare_db_for_update_job
    response = client.patch(
        f"{POST_JOBS_PATH}/{UPDATE_JOB_IDS[0]}",
        json={field: new_value},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 204
    updated_job = session.query(Job).get(UPDATE_JOB_IDS[0])
    assert str(updated_job.__dict__[field]) == new_value
    assert response.text == ""


@mark.integration
@mark.parametrize(
    ["query", "status_code"],
    [
        ({"wrong_field": "some_value"}, 204),  # not in model and patch schema
        ({"job_id": "some_value"}, 204),  # not in patch schema
        ({"is_auto_distribution": "some_value"}, 204),  # not in patch schema
        ({"tenant": "some_value"}, 204),  # not in patch schema
        ({"validation_type": "some_value"}, 204),  # not in patch schema
        ({"tasks": "some_value"}, 204),  # not in patch schema
        ({"categories": 1}, 422),  # in patch schema, wrong type
        ({}, 204),  # empty query
    ],
)
def test_update_wrong_fields(query, status_code, prepare_db_for_update_job):
    """Tests that empty query or query with wrong fields will not modify job
    in database and checks appropriate status codes."""
    session = prepare_db_for_update_job
    old_job = session.query(Job).get(UPDATE_JOB_IDS[0])
    response = client.patch(
        f"{POST_JOBS_PATH}/{UPDATE_JOB_IDS[0]}",
        json=query,
        headers=TEST_HEADERS,
    )
    assert response.status_code == status_code
    updated_job = session.query(Job).get(UPDATE_JOB_IDS[0])
    assert old_job.__dict__ == updated_job.__dict__


@mark.integration
@mark.parametrize("job_id", (UPDATE_JOB_IDS[3], UPDATE_WRONG_JOB_ID))
def test_update_wrong_job_id(job_id, prepare_db_for_update_job):
    """Tests that request to change job with not-existing job_id or other
    tenant's job will return 404 error.
    """
    response = client.patch(
        f"{POST_JOBS_PATH}/{job_id}",
        json={"deadline": "2022-10-19T01:01:01"},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 404
    assert f"Error: Job with job_id ({job_id}) not found" in response.text


@mark.integration
@mark.parametrize(
    ["category_ids", "job_id"],
    (
        [["1"], UPDATE_JOB_IDS[0]],
        [["1", "2"], UPDATE_JOB_IDS[0]],
        [["2"], UPDATE_JOB_IDS[0]],
        (["1"], UPDATE_JOB_IDS[7]),
    ),
)
def test_update_categories(category_ids, prepare_db_for_update_job, job_id):
    """Checks status 204 code and 'association_job_category' table entities
    for job's appropriate categories update cases. Also checks that categories
    were affected only in 'association_job_category' table but not in
    'categories' table itself.
    """
    session = prepare_db_for_update_job
    all_categories_before = session.query(Category).all()
    response = client.patch(
        f"{POST_JOBS_PATH}/{job_id}",
        json={"categories": category_ids},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 204
    jobs_categories = (
        session.query(association_job_category)
        .filter_by(job_id=job_id)
        .order_by(asc("category_id"))
        .all()
    )
    expected_categories = [
        (category_id, job_id) for category_id in category_ids
    ]
    assert jobs_categories == expected_categories
    all_categories_after = session.query(Category).all()
    assert all_categories_before == all_categories_after


@mark.integration
@mark.parametrize("category_ids", ("3", "4"))
def test_update_wrong_categories(category_ids, prepare_db_for_update_job):
    """Checks status 404 code and association_job_category entities for
    not-exist and other tenant's categories update cases.
    """
    session = prepare_db_for_update_job
    response = client.patch(
        f"{POST_JOBS_PATH}/{UPDATE_JOB_IDS[0]}",
        json={"categories": list(category_ids)},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 404
    jobs_categories = (
        session.query(association_job_category)
        .filter_by(job_id=UPDATE_JOB_IDS[0])
        .all()
    )
    assert f"No such categories: {category_ids}." in response.text
    assert jobs_categories == [(CATEGORIES_IDS[0], UPDATE_JOB_IDS[0])]


@mark.integration
@mark.parametrize(
    ["field", "job_id", "new_files"],
    [
        ("files", UPDATE_JOB_IDS[0], [UPDATE_JOB_FILES_FROM_ASSETS[0]]),
        ("files", UPDATE_JOB_IDS[0], UPDATE_JOB_FILES_FROM_ASSETS[:1]),
        ("files", UPDATE_JOB_IDS[0], [UPDATE_JOB_FILES_FROM_ASSETS[2]]),
        ("datasets", UPDATE_JOB_IDS[0], [UPDATE_JOB_FILES_FROM_ASSETS[2]]),
        ("files", UPDATE_JOB_IDS[7], [UPDATE_JOB_FILES_FROM_ASSETS[2]]),
    ],
)
def test_update_files(
    prepare_db_for_update_job, monkeypatch, field, job_id, new_files
):
    """Checks that files for job successfully update with 204 response both
    from 'files' and 'dataset' fields and that old job's files delete from
    'files' table. Also checks that files with same id as deleted/added for
    this job will be not affected for other job.
    """
    session = prepare_db_for_update_job
    expected_result = new_files
    new_ids = [new_id["file_id"] for new_id in new_files]
    monkeypatch.setattr(
        "annotation.jobs.services.get_files_info",
        Mock(return_value=new_files),
    )
    response = client.patch(
        f"{POST_JOBS_PATH}/{job_id}",
        json={field: new_ids},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 204
    job_files_db = (
        session.query(File)
        .filter_by(job_id=job_id)
        .order_by(asc(File.file_id))
        .all()
    )
    job_files = [
        {"file_id": job_file.file_id, "pages_number": job_file.pages_number}
        for job_file in job_files_db
    ]
    assert job_files == expected_result
    other_job_files = (
        session.query(File).filter_by(job_id=UPDATE_JOB_IDS[2]).first()
    )  # check that others job file wasn't deleted even if file_id is the same
    assert row_to_dict(other_job_files) == row_to_dict(UPDATE_JOB_FILES[1])


@mark.integration
@mark.parametrize(
    ["user_type", "old_user_id", "new_user_ids", "expected_users_count"],
    [
        ("annotators", USER_IDS[0], [USER_IDS[0]], 4),  # same user
        ("annotators", USER_IDS[0], [USER_IDS[1]], 4),  # other user role
        ("annotators", USER_IDS[0], [USER_IDS[3]], 4),  # user without job
        ("annotators", USER_IDS[0], [UPDATE_NEW_USER_ID], 5),  # new user
        ("annotators", USER_IDS[0], [USER_IDS[0], USER_IDS[1]], 4),  # multiple
        ("validators", USER_IDS[1], [USER_IDS[0]], 4),
        ("validators", USER_IDS[1], [USER_IDS[0], UPDATE_NEW_USER_ID], 5),
        ("owners", USER_IDS[2], [USER_IDS[1]], 4),
        ("owners", USER_IDS[2], [USER_IDS[1], UPDATE_NEW_USER_ID], 5),
    ],
)
def test_update_job_new_user(
    prepare_db_for_update_job,
    user_type,
    old_user_id,
    new_user_ids,
    expected_users_count,
):
    """Tests updating of different user role fields (annotators, validators
    and owners) for both existing users and new users. Checks entities changing
    for job_id in association_table and in 'users' table itself (when new user
    was added into database).
    """
    session = prepare_db_for_update_job
    existing_users_count = session.query(User).count()
    assert existing_users_count == 4
    association_table = ASSOCIATION_TABLES[user_type]
    old_association = (
        session.query(association_table)
        .filter_by(job_id=UPDATE_JOB_IDS[1])
        .first()
    )
    assert str(old_association.user_id) == old_user_id
    response = client.patch(
        f"{POST_JOBS_PATH}/{UPDATE_JOB_IDS[1]}",
        json={user_type: new_user_ids},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 204
    new_users_count = session.query(User).count()
    assert new_users_count == expected_users_count
    new_association = (
        session.query(association_table)
        .filter_by(job_id=UPDATE_JOB_IDS[1])
        .order_by(asc("user_id"))
        .all()
    )
    assert [str(user.user_id) for user in new_association] == new_user_ids


@mark.integration
@mark.parametrize(
    ["user_type", "user_ids", "job_id", "status_code", "error_message"],
    [
        (
            "annotators",
            [],
            UPDATE_JOB_IDS[0],
            400,
            "There must be more than one annotator provided for cross",
        ),
        (
            "annotators",
            [USER_IDS[0]],
            UPDATE_JOB_IDS[0],
            400,
            "There must be more than one annotator provided for cross",
        ),
        (
            "validators",
            [USER_IDS[1]],
            UPDATE_JOB_IDS[0],
            400,
            "type is cross validation, no validators should be provided",
        ),
        (
            "annotators",
            [],
            UPDATE_JOB_IDS[1],
            400,
            "at least one annotator provided for hierarchical validation",
        ),
        (
            "validators",
            [],
            UPDATE_JOB_IDS[1],
            400,
            "validation type is hierarchical, validators should be provided",
        ),
        (
            "annotators",
            [USER_IDS[1]],
            UPDATE_JOB_IDS[4],
            400,
            "type is validation_only, no annotators should be provided.",
        ),
        (
            "validators",
            [],
            UPDATE_JOB_IDS[4],
            400,
            "type is validation_only, validators should be provided.",
        ),
        (
            #  Update job users for import job
            "annotators",
            [USER_IDS[1]],
            UPDATE_JOB_IDS[7],
            400,
            "There should be no annotators or validators provided "
            "for ImportJob",
        ),
    ],
)
def test_update_user_constraints(
    monkeypatch,
    prepare_db_for_update_job,
    user_type,
    user_ids,
    job_id,
    status_code,
    error_message,
):
    """Tests updating of different user role fields (annotators, validators
    and owners) for both existing users and new users. Checks entities changing
    for job_id in association_table and in 'users' table itself (when new user
    was added into database).
    """
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value={job_id: "JobName"}),
    )
    response = client.patch(
        f"{POST_JOBS_PATH}/{job_id}",
        json={user_type: user_ids},
        headers=TEST_HEADERS,
    )
    assert response.status_code == status_code
    assert error_message in response.text


@mark.integration
@mark.parametrize("field", ["files", "datasets"])
def test_update_files_and_datasets_for_already_started_job(
    monkeypatch, prepare_db_for_update_job, field
):
    """Tests that update of job which in progress status
    with files or datasets is restricted"""
    expected_code = 422
    error_message = (
        "files and datasets can't be updated for already started job"
    )
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value={UPDATE_JOB_IDS[5]: "JobName"}),
    )
    response = client.patch(
        f"{POST_JOBS_PATH}/{ UPDATE_JOB_IDS[5]}",
        json={field: [1, 2]},
        headers=TEST_HEADERS,
    )
    assert response.status_code == expected_code
    assert error_message in response.text


@mark.integration
@mark.parametrize(
    ["user_type", "new_user_ids", "expected_code", "expected_users_count"],
    [
        ("annotators", [USER_IDS[0]], 400, 1),
        ("annotators", [], 204, 1),
        ("validators", [USER_IDS[0], UPDATE_NEW_USER_ID], 400, 1),
        ("validators", [], 204, 1),
        ("owners", [], 204, 0),
        ("owners", [USER_IDS[1], UPDATE_NEW_USER_ID], 204, 2),
    ],
)
def test_update_extraction_job_new_user(
    monkeypatch,
    prepare_db_for_update_job,
    user_type,
    new_user_ids,
    expected_code,
    expected_users_count,
):
    """Tests updating different user fields (annotators, validators and owners)
    for both existing users and new users in automatic ExtractionJob. Checks
    that passed annotators or validators will raise error with 400 response
    status code and entities changing in association_job_owner and in 'users'
    table itself (when new owner was added).
    """
    tables = (
        association_job_annotator,
        association_job_validator,
        association_job_owner,
    )
    session = prepare_db_for_update_job
    job_id = UPDATE_JOB_IDS[6]
    existing_users_count = sum(
        session.query(table).filter_by(job_id=job_id).count()
        for table in tables
    )
    assert existing_users_count == 1
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value={job_id: "JobName"}),
    )
    response = client.patch(
        f"{POST_JOBS_PATH}/{job_id}",
        json={user_type: new_user_ids},
        headers=TEST_HEADERS,
    )
    assert response.status_code == expected_code
    new_users_count = sum(
        session.query(table).filter_by(job_id=job_id).count()
        for table in tables
    )
    assert new_users_count == expected_users_count


@mark.integration
def test_delete_redundant_users(prepare_db_for_update_job):
    """Tests redundant user deletion"""
    # Add redundant user to job
    client.patch(
        f"{POST_JOBS_PATH}/{1}",
        json={"annotators": [USER_IDS[0], USER_IDS[3]]},
        headers=TEST_HEADERS,
    )
    #  Delete redundant user with new patch
    response = client.patch(
        f"{POST_JOBS_PATH}/{1}",
        json={"annotators": [USER_IDS[0], USER_IDS[1]]},
        headers=TEST_HEADERS,
    )
    prepare_db_for_update_job.commit()
    redundant_user = (
        prepare_db_for_update_job.query(User)
        .filter(User.user_id == USER_IDS[3])
        .all()
    )
    assert not redundant_user
    assert response.status_code == 204


@mark.integration
def test_not_delete_redundant_user_as_owner_of_another_job(
    prepare_db_for_update_job,
):
    """Tests that redundant user has not been
    deleted because he's owner of another job"""
    response = client.patch(
        f"{POST_JOBS_PATH}/1",
        json={"annotators": [USER_IDS[0], USER_IDS[1]]},
        headers=TEST_HEADERS,
    )
    prepare_db_for_update_job.commit()
    redundant_user_owner = (
        prepare_db_for_update_job.query(User)
        .filter(User.user_id == USER_IDS[2])
        .all()
    )
    assert redundant_user_owner
    assert response.status_code == 204


@mark.integration
@responses.activate
@mark.parametrize(
    ["job_id", "tenant", "token", "expected_result"],
    [
        (UPDATE_JOB_IDS[0], UPDATE_JOBS[0].tenant, TEST_TOKEN, "JobName1"),
        (UPDATE_JOB_IDS[1], UPDATE_JOBS[1].tenant, TEST_TOKEN, "JobName2"),
        (UPDATE_JOB_IDS[2], UPDATE_JOBS[2].tenant, TEST_TOKEN, "JobName3"),
    ],
)
def test_update_jobs_name_from_db_or_microservice(
    monkeypatch,
    prepare_db_for_update_job,
    job_id,
    tenant,
    token,
    expected_result,
):
    """
    Tests job's name update with patch of the job in cases name presented in db
    or name field is empty
    """
    session = prepare_db_for_update_job
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value={3: "JobName3"}),
    )
    response = client.patch(
        f"{POST_JOBS_PATH}/{job_id}",
        json={"deadline": "2022-09-19T01:01:01"},
        headers=TEST_HEADERS,
    )
    job_name = session.query(Job.name).filter(Job.job_id == job_id).scalar()
    assert response.status_code == 204
    assert job_name == expected_result


REDISTRIBUTE_TASKS_USERS = [
    "11ec1df0-516d-4905-a902-fbd1ed99a49d",
    "12ec1df0-526d-4905-a902-fbd1ed99a49d",
    "13ec1df0-536d-4905-a902-fbd1ed99a49d",
    "14ec1df0-546d-4905-a902-fbd1ed99a49d",
]
NEW_REDISTRIBUTE_TASKS_USER = User(
    user_id="15ec1df0-556d-4905-a902-fbd1ed99a49d"
)
REDISTRIBUTE_TASKS_CATEGORIES = [
    Category(id="Test123", name="Test1", type=CategoryTypeSchema.box),
    Category(id="Test234", name="Test2", type=CategoryTypeSchema.box),
]
NEW_REDISTRIBUTE_TASKS_CATEGORY = Category(
    id="Test345", name="Test2", type=CategoryTypeSchema.box
)
REDISTRIBUTE_TASKS_FILE = File(
    file_id=654321,
    tenant=TEST_TENANT,
    job_id=1234567,
    pages_number=6,
    distributed_annotating_pages=[6],
    annotated_pages=[1, 2],
    distributed_validating_pages=[6],
    status=FileStatusEnumSchema.pending,
)
REDISTRIBUTE_TASKS_JOB = Job(
    job_id=REDISTRIBUTE_TASKS_FILE.job_id,
    callback_url="http://www.test.com/test1",
    annotators=[
        User(user_id=REDISTRIBUTE_TASKS_USERS[0]),
        User(user_id=REDISTRIBUTE_TASKS_USERS[1]),
        User(user_id=REDISTRIBUTE_TASKS_USERS[2]),
    ],
    validators=[User(user_id=REDISTRIBUTE_TASKS_USERS[3])],
    validation_type=ValidationSchema.extensive_coverage,
    extensive_coverage=2,
    files=[REDISTRIBUTE_TASKS_FILE],
    is_auto_distribution=True,
    categories=REDISTRIBUTE_TASKS_CATEGORIES,
    deadline=None,
    tenant=TEST_TENANT,
    status=JobStatusEnumSchema.in_progress,
)
NEW_EXTENSIVE_COVERAGE = 3
REDISTRIBUTED_TASKS = [
    {
        "id": 11,
        "file_id": REDISTRIBUTE_TASKS_FILE.file_id,
        "pages": [1, 2],
        "job_id": REDISTRIBUTE_TASKS_FILE.job_id,
        "user_id": REDISTRIBUTE_TASKS_USERS[0],
        "is_validation": False,
        "status": TaskStatusEnumSchema.finished,
        "deadline": None,
    },
    {
        "id": 12,
        "file_id": REDISTRIBUTE_TASKS_FILE.file_id,
        "pages": [1, 2],
        "job_id": REDISTRIBUTE_TASKS_FILE.job_id,
        "user_id": REDISTRIBUTE_TASKS_USERS[1],
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    },
    {
        "id": 21,
        "file_id": REDISTRIBUTE_TASKS_FILE.file_id,
        "pages": [3, 4],
        "job_id": REDISTRIBUTE_TASKS_FILE.job_id,
        "user_id": REDISTRIBUTE_TASKS_USERS[1],
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    },
    {
        "id": 22,
        "file_id": REDISTRIBUTE_TASKS_FILE.file_id,
        "pages": [3, 4],
        "job_id": REDISTRIBUTE_TASKS_FILE.job_id,
        "user_id": REDISTRIBUTE_TASKS_USERS[2],
        "is_validation": False,
        "status": TaskStatusEnumSchema.ready,
        "deadline": None,
    },
    {
        "id": 31,
        "file_id": REDISTRIBUTE_TASKS_FILE.file_id,
        "pages": [5, 6],
        "job_id": REDISTRIBUTE_TASKS_FILE.job_id,
        "user_id": REDISTRIBUTE_TASKS_USERS[2],
        "is_validation": False,
        "status": TaskStatusEnumSchema.ready,
        "deadline": None,
    },
    {
        "id": 32,
        "file_id": REDISTRIBUTE_TASKS_FILE.file_id,
        "pages": [5, 6],
        "job_id": REDISTRIBUTE_TASKS_FILE.job_id,
        "user_id": REDISTRIBUTE_TASKS_USERS[1],
        "is_validation": False,
        "status": TaskStatusEnumSchema.ready,
        "deadline": None,
    },
    {
        "id": 41,
        "file_id": REDISTRIBUTE_TASKS_FILE.file_id,
        "pages": [1, 2, 3, 4, 5, 6],
        "job_id": REDISTRIBUTE_TASKS_FILE.job_id,
        "user_id": REDISTRIBUTE_TASKS_USERS[3],
        "is_validation": True,
        "status": TaskStatusEnumSchema.pending,
        "deadline": None,
    },
]


@mark.integration
def test_update_jobs_delete_annotator(
    monkeypatch, prepare_db_for_redistribute_tasks
):
    session = prepare_db_for_redistribute_tasks
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value={REDISTRIBUTE_TASKS_JOB.job_id: "job_name"}),
    )

    response = client.patch(
        f"{POST_JOBS_PATH}/{REDISTRIBUTE_TASKS_JOB.job_id}",
        json={
            "annotators": [
                REDISTRIBUTE_TASKS_USERS[1],
                REDISTRIBUTE_TASKS_USERS[2],
                NEW_REDISTRIBUTE_TASKS_USER.user_id,
            ],
            "categories": [
                *[category.id for category in REDISTRIBUTE_TASKS_CATEGORIES],
                NEW_REDISTRIBUTE_TASKS_CATEGORY.id,
            ],
            "extensive_coverage": NEW_EXTENSIVE_COVERAGE,
        },
        headers=TEST_HEADERS,
    )

    assert response.status_code == 204

    tasks = (
        session.query(ManualAnnotationTask)
        .filter_by(job_id=REDISTRIBUTE_TASKS_JOB.job_id)
        .all()
    )
    job = (
        session.query(Job)
        .filter_by(job_id=REDISTRIBUTE_TASKS_JOB.job_id)
        .all()
    )
    job_file = (
        session.query(File)
        .filter_by(job_id=REDISTRIBUTE_TASKS_JOB.job_id)
        .all()
    )

    assert any(
        task for task in tasks if task.id == REDISTRIBUTED_TASKS[0]["id"]
    )
    assert all(
        task.status
        in {
            TaskStatusEnumSchema.ready,
            TaskStatusEnumSchema.in_progress,
            TaskStatusEnumSchema.finished,
        }
        for task in tasks
        if not task.is_validation
    )

    pages_for_annotation = [
        page for task in tasks if not task.is_validation for page in task.pages
    ]
    pages_counter = Counter(pages_for_annotation)
    assert len(pages_counter) == REDISTRIBUTE_TASKS_FILE.pages_number
    assert all(
        value == NEW_EXTENSIVE_COVERAGE for value in pages_counter.values()
    )

    pages_for_validation = [
        page for task in tasks if task.is_validation for page in task.pages
    ]
    assert len(pages_for_validation) == REDISTRIBUTE_TASKS_FILE.pages_number

    assert (
        session.query(Category)
        .filter_by(id=NEW_REDISTRIBUTE_TASKS_CATEGORY.id)
        .first()
        in job[0].categories
    )
    assert (
        job_file[0].distributed_annotating_pages
        == job_file[0].distributed_validating_pages
    )
