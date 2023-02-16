from unittest.mock import Mock

import responses
from fastapi.testclient import TestClient
from pytest import mark, raises
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.jobs import update_user_overall_load
from annotation.main import app
from annotation.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
)
from annotation.models import (
    AnnotatedDoc,
    Category,
    File,
    Job,
    ManualAnnotationTask,
    User,
)
from annotation.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    JobTypeEnumSchema,
    ValidationSchema,
)
from tests.consts import CRUD_TASKS_PATH, FINISH_TASK_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT
from tests.test_tasks_crud_ud import construct_path

client = TestClient(app)

OVERALL_LOAD_USERS = [
    # user without initial tasks
    User(user_id="f0474853-f733-41c0-b897-90b788b822e3"),
    # user with one initial task for post
    User(user_id="b44156f8-e634-48a6-b5f3-c8b1462a2d67"),
    # user with two initial tasks for delete
    User(user_id="c45156f8-e634-48a6-b5f3-c8b1462a2d67"),
    # users for delete_batch_tasks, finish task
    User(user_id="d0574857-f733-41c0-b897-90b788b822e4"),  # annotator
    User(user_id="3082242e-15e3-4e18-aad0-e3bf182b8550"),  # 1st validator
    User(user_id="4e9c5839-f63b-49c8-b918-614b87813e53"),  # 2nd validator
    # users without tasks for distribution, save job
    User(user_id="5e9c5839-f63b-49c8-b918-614b87813e53"),
    User(user_id="6782242e-15e3-4e18-aad0-e3bf182b8551"),
    # third user for save job autodistribution
    User(user_id="a44156f8-e634-48a6-b5f3-c8b1462a2d67"),
    # users for distribution for particular job, job_id 4
    User(user_id="a14156f8-e634-48a6-b5f3-c8b1462a2d67"),
    User(user_id="a24156f8-e634-48a6-b5f3-c8b1462a2d67"),
    User(user_id="a34156f8-e634-48a6-b5f3-c8b1462a2d67"),
    # annotator for job patch, job with auto_distribution
    User(user_id="a44156f8-e634-48a6-b5f3-c8b1462a2d67"),
    # validator for job patch, job with auto_distribution
    User(user_id="a54156f8-e634-48a6-b5f3-c8b1462a2d67"),
    # owner for job patch, job with auto_distribution
    User(user_id="a64156f8-e634-48a6-b5f3-c8b1462a2d67"),
]
TASK_FILES_OVERALL_LOAD = [
    File(
        file_id=5,
        tenant=TEST_TENANT,
        job_id=2,
        pages_number=9,
        annotated_pages=[3, 4, 5, 6],
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=5,
        tenant=TEST_TENANT,
        job_id=2,
        pages_number=9,
        annotated_pages=[7, 8, 9],
        validated_pages=[7, 8, 9],
        status=FileStatusEnumSchema.annotated,
    ),
    File(file_id=3, tenant=TEST_TENANT, job_id=3, pages_number=4),
    File(file_id=6, tenant=TEST_TENANT, job_id=1, pages_number=20),
    File(file_id=7, tenant=TEST_TENANT, job_id=1, pages_number=30),
    File(file_id=9, tenant=TEST_TENANT, job_id=4, pages_number=30),
    File(
        file_id=10,
        tenant=TEST_TENANT,
        job_id=5,
        pages_number=6,
        status=FileStatusEnumSchema.pending,
    ),
]
OVERALL_LOAD_JOBS = [
    Job(
        job_id=1,
        callback_url="http://www.test.com",
        annotators=[user for user in OVERALL_LOAD_USERS[:3]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=[
            Category(id="123", name="Title", type=CategoryTypeSchema.box)
        ],
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    # job for delete_batch_tasks
    Job(
        job_id=2,
        callback_url="http://www.test.com",
        annotators=[user for user in OVERALL_LOAD_USERS[3:6]],
        validators=[user for user in OVERALL_LOAD_USERS[3:6]],
        validation_type=ValidationSchema.hierarchical,
        files=[TASK_FILES_OVERALL_LOAD[0]],
        is_auto_distribution=False,
        categories=[
            Category(id="125", name="Paragraph", type=CategoryTypeSchema.box)
        ],
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    # job for task distribution
    Job(
        job_id=3,
        callback_url="http://www.test.com",
        annotators=[user for user in OVERALL_LOAD_USERS[6:8]],
        validation_type=ValidationSchema.cross,
        files=[TASK_FILES_OVERALL_LOAD[2]],
        is_auto_distribution=False,
        categories=[
            Category(id="126", name="Abstract", type=CategoryTypeSchema.box)
        ],
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),  # job for task distribution for particular job
    Job(
        job_id=4,
        callback_url="http://www.test.com",
        annotators=[user for user in OVERALL_LOAD_USERS[9:12]],
        validators=[user for user in OVERALL_LOAD_USERS[9:12]],
        validation_type=ValidationSchema.hierarchical,
        files=[TASK_FILES_OVERALL_LOAD[5]],
        is_auto_distribution=False,
        categories=[
            Category(id="127", name="Abstract", type=CategoryTypeSchema.box)
        ],
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=5,  # hierarchical job with auto_distribution
        callback_url="http://www.test.com/test2",
        annotators=[OVERALL_LOAD_USERS[12]],
        validators=[OVERALL_LOAD_USERS[13]],
        owners=[OVERALL_LOAD_USERS[14]],
        validation_type=ValidationSchema.hierarchical,
        is_auto_distribution=True,
        categories=[
            Category(id="128", name="Abstract", type=CategoryTypeSchema.box)
        ],
        deadline="2022-10-19T01:01:01",
        tenant=TEST_TENANT,
        status=JobStatusEnumSchema.in_progress,
    ),
]
# jobs for save job autodistribution
NEW_OVERALL_LOAD_JOB_CROSS = {
    "callback_url": "http://www.test.com/",
    "annotators": [user.user_id for user in OVERALL_LOAD_USERS[6:8]],
    "validators": [],
    "owners": [],
    "validation_type": ValidationSchema.cross,
    "files": [8],
    "datasets": [],
    "is_auto_distribution": True,
    "categories": ["126"],
    "deadline": "2021-10-19T01:01:01",
    "job_type": JobTypeEnumSchema.AnnotationJob,
}
NEW_OVERALL_LOAD_JOB_HIERARCHICAL = {
    "callback_url": "http://www.test.com/",
    "annotators": [user.user_id for user in OVERALL_LOAD_USERS[6:9]],
    "validators": [user.user_id for user in OVERALL_LOAD_USERS[6:9]],
    "owners": [],
    "validation_type": ValidationSchema.hierarchical,
    "files": [8],
    "datasets": [],
    "is_auto_distribution": True,
    "categories": ["126"],
    "deadline": "2021-10-19T01:01:01",
    "job_type": JobTypeEnumSchema.AnnotationJob,
}
OVERALL_LOAD_CREATED_TASKS = [
    # task for the second user
    ManualAnnotationTask(
        file_id=6,
        is_validation=False,
        job_id=1,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        status="Pending",
        user_id=OVERALL_LOAD_USERS[1].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    # tasks for the third user
    # task_id == 2
    ManualAnnotationTask(
        file_id=6,
        is_validation=False,
        job_id=1,
        pages=[16, 17, 18, 19, 20],
        status="Ready",
        user_id=OVERALL_LOAD_USERS[2].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    # task_id == 3
    ManualAnnotationTask(
        file_id=6,
        is_validation=False,
        job_id=1,
        pages=[21, 22],
        status="Ready",
        user_id=OVERALL_LOAD_USERS[2].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    # tasks for delete_batch_task
    # task_id == 4
    ManualAnnotationTask(
        file_id=5,
        is_validation=False,
        job_id=2,
        pages=[1, 2],
        status="Ready",
        user_id=OVERALL_LOAD_USERS[3].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    # task_id == 5
    ManualAnnotationTask(
        file_id=5,
        is_validation=False,
        job_id=2,
        pages=[3, 4, 5, 6],
        status="In Progress",
        user_id=OVERALL_LOAD_USERS[3].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    # task_id == 6
    ManualAnnotationTask(
        file_id=5,
        is_validation=True,
        job_id=2,
        pages=[3, 4, 5, 6],
        status="Pending",
        user_id=OVERALL_LOAD_USERS[4].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    # task_id == 7
    ManualAnnotationTask(
        file_id=5,
        is_validation=True,
        job_id=2,
        pages=[7, 8, 9],
        status="In Progress",
        user_id=OVERALL_LOAD_USERS[5].user_id,
        deadline="2021-10-19T01:01:01",
    ),
]
OVERALL_LOAD_NEW_TASKS = [
    {
        "file_id": 7,
        "is_validation": False,
        "job_id": 1,
        "pages": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
        "user_id": OVERALL_LOAD_USERS[0].user_id,
        "deadline": "2021-12-12T01:01:01",
    },
    {
        "file_id": 7,
        "is_validation": False,
        "job_id": 1,
        "pages": [16, 17, 18, 19, 20],
        "user_id": OVERALL_LOAD_USERS[1].user_id,
        "deadline": "2021-12-12T01:01:01",
    },
    {
        "user_ids": [str(user.user_id) for user in OVERALL_LOAD_USERS[6:8]],
        "files": [3],
        "datasets": [],
        "job_id": 3,
    },
]
VALIDATED_DOC_OVERALL_LOAD = AnnotatedDoc(
    revision="1",
    user=OVERALL_LOAD_USERS[5].user_id,
    pipeline=None,
    file_id=5,
    job_id=2,
    pages={},
    validated=[7],
    failed_validation_pages=[8, 9],
    tenant=TEST_TENANT,
    task_id=7,
    date="2021-09-19T01:01:01",
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
            "id": 8,
            "original_name": "some.pdf",
            "bucket": "test",
            "size_in_bytes": 165887,
            "extension": ".pdf",
            "content_type": "image/png",
            "pages": 12,
            "last_modified": "2021-10-24T01:11:11",
            "status": "uploaded",
            "path": "files/8/8.pdf",
            "datasets": [],
        }
    ],
}


@mark.integration
@mark.parametrize(
    ["task_info", "expected_overall_load"],
    [
        # user doesn`t have another tasks, current overall_load = 0
        (OVERALL_LOAD_NEW_TASKS[0], 10),
        # user has another task, current overall_load = 15
        (OVERALL_LOAD_NEW_TASKS[1], 20),
    ],
)
def test_update_overall_load_after_post_task(
    prepare_db_for_overall_load, task_info, expected_overall_load
):
    response = client.post(
        "{0}".format(CRUD_TASKS_PATH), json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == 201

    user = prepare_db_for_overall_load.query(User).get(task_info["user_id"])
    assert user.overall_load == expected_overall_load


@mark.integration
@mark.parametrize(
    ["task_id", "request_body", "users_id", "expected_overall_loads"],
    [
        (1, {"pages": [7, 8, 9]}, [OVERALL_LOAD_USERS[1].user_id], [3]),
        (  # replace 1st user
            1,
            {"user_id": OVERALL_LOAD_USERS[0].user_id},
            [OVERALL_LOAD_USERS[1].user_id, OVERALL_LOAD_USERS[0].user_id],
            [0, 15],
        ),
    ],
)
def test_overall_load_after_update_task(
    prepare_db_for_overall_load,
    task_id,
    request_body,
    users_id,
    expected_overall_loads,
):
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task_id),
        json=request_body,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 200

    for user_id, expected_overall_load in zip(
        users_id, expected_overall_loads
    ):
        user = prepare_db_for_overall_load.query(User).get(user_id)
        assert user.overall_load == expected_overall_load


@mark.integration
@mark.parametrize(
    ["task_id", "user_id", "expected_overall_load"],
    [
        (1, OVERALL_LOAD_USERS[1].user_id, 0),  # user has one task
        (2, OVERALL_LOAD_USERS[2].user_id, 2),  # user has two tasks
    ],
)
def test_overall_load_after_delete_task(
    prepare_db_for_overall_load, task_id, user_id, expected_overall_load
):
    response = client.delete(
        construct_path(CRUD_TASKS_PATH, task_id), headers=TEST_HEADERS
    )
    assert response.status_code == 204
    user = prepare_db_for_overall_load.query(User).get(user_id)
    assert user.overall_load == expected_overall_load


@mark.integration
def test_overall_load_after_delete_batch_tasks(prepare_db_for_overall_load):
    user_ids = [
        OVERALL_LOAD_CREATED_TASKS[3].user_id,
        OVERALL_LOAD_CREATED_TASKS[5].user_id,
    ]
    expected_overall_loads = [4, 0]
    response = client.delete(
        CRUD_TASKS_PATH, json=[4, 6], headers=TEST_HEADERS
    )
    assert response.status_code == 204
    for user_id, expected_overall_load in zip(
        user_ids, expected_overall_loads
    ):
        user = prepare_db_for_overall_load.query(User).get(user_id)
        assert user.overall_load == expected_overall_load


@mark.integration
@mark.parametrize(
    ["task_id", "url_params", "users_id", "expected_overall_loads"],
    [
        (  # annotator has another task
            5,
            {},
            [OVERALL_LOAD_USERS[3].user_id],
            [2],
        ),
        (  # validator with pages for reannotation
            7,
            {
                "annotation_user_for_failed_pages": OVERALL_LOAD_USERS[
                    4
                ].user_id
            },
            [OVERALL_LOAD_USERS[5].user_id, OVERALL_LOAD_USERS[4].user_id],
            [1, 6],
        ),
    ],
)
def test_overall_load_after_finish_task(
    prepare_db_for_overall_load,
    task_id,
    url_params,
    users_id,
    expected_overall_loads,
):
    response = client.post(
        FINISH_TASK_PATH.format(task_id=task_id),
        json=url_params,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 200
    for user_id, expected_overall_load in zip(
        users_id, expected_overall_loads
    ):
        user = prepare_db_for_overall_load.query(User).get(user_id)
        assert user.overall_load == expected_overall_load


@mark.integration
def test_overall_load_after_distribution(
    monkeypatch, prepare_db_for_overall_load
):
    monkeypatch.setattr(
        "app.microservice_communication.assets_communication.get_response",
        Mock(return_value=[{"id": 3, "pages": 4}]),
    )
    response = client.post(
        "/distribution", json=OVERALL_LOAD_NEW_TASKS[2], headers=TEST_HEADERS
    )
    assert response.status_code == 201
    user = prepare_db_for_overall_load.query(User).get(
        OVERALL_LOAD_USERS[6].user_id
    )
    assert user.overall_load == 4


@mark.integration
@mark.parametrize(
    ["job_id", "users", "expected_result"],
    [  # initially users` overall_loads 0
        (3, OVERALL_LOAD_USERS[6:8], (4, 4)),  # cross validation
        (4, OVERALL_LOAD_USERS[9:12], (20, 20, 20)),  # hierarchical
    ],
)
def test_overall_load_after_distribution_job(
    prepare_db_for_overall_load, job_id, users, expected_result
):
    response = client.post(f"distribution/{job_id}", headers=TEST_HEADERS)
    assert response.status_code == 201
    for user, result in zip(users, expected_result):
        user = prepare_db_for_overall_load.query(User).get(user.user_id)
        assert user.overall_load == result


@mark.integration
@responses.activate
@mark.parametrize(
    ["new_job", "users", "expected_result"],
    [  # initially users` overall_loads 0
        (  # cross validation job
            NEW_OVERALL_LOAD_JOB_CROSS,
            OVERALL_LOAD_USERS[6:8],
            (12, 12),
        ),
        (  # hierarchical validation job
            NEW_OVERALL_LOAD_JOB_HIERARCHICAL,
            OVERALL_LOAD_USERS[6:9],
            (8, 8, 8),
        ),
    ],
)
def test_overall_load_save_job_autodistribution(
    prepare_db_for_overall_load, new_job, users, expected_result
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=DATASET_MANAGER_FILE_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        f"jobs/{6}",
        json=new_job,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 201
    for user, result in zip(users, expected_result):
        user = prepare_db_for_overall_load.query(User).get(user.user_id)
        assert user.overall_load == result


@mark.integration
def test_update_user_overall_load(prepare_db_for_overall_load):
    user_id = OVERALL_LOAD_USERS[1].user_id

    task = (
        prepare_db_for_overall_load.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.user_id == user_id)
        .first()
    )
    task.pages.extend([16, 17])
    prepare_db_for_overall_load.flush()

    update_user_overall_load(prepare_db_for_overall_load, user_id)
    prepare_db_for_overall_load.commit()

    user = prepare_db_for_overall_load.query(User).get(user_id)
    assert user.overall_load == 17


@mark.integration
@mark.parametrize(
    ["db_annotator_custom_overall_load", "change_value", "expected_load"],
    [
        (1, 2, 3),
        (2, -2, 0),
    ],
    indirect=["db_annotator_custom_overall_load"],
)
def test_overall_change(
    db_annotator_custom_overall_load: Session,
    change_value,
    expected_load,
):
    session = db_annotator_custom_overall_load
    annotator = session.query(User).get(OVERALL_LOAD_USERS[0].user_id)
    annotator.overall_load += change_value
    session.commit()
    annotator = session.query(User).get(OVERALL_LOAD_USERS[0].user_id)
    assert annotator.overall_load == expected_load


@mark.integration
@mark.parametrize("db_annotator_custom_overall_load", [0], indirect=True)
def test_not_negative_constraint(db_annotator_custom_overall_load: Session):
    session = db_annotator_custom_overall_load
    annotator = session.query(User).get(OVERALL_LOAD_USERS[0].user_id)
    annotator.overall_load -= 1
    with raises(SQLAlchemyError, match=r".*not_negative_overall_load.*"):
        session.commit()
    session.rollback()


@mark.integration
@mark.parametrize(
    ["job_id", "users", "expected_overall_load"],
    [
        (
            OVERALL_LOAD_JOBS[4].job_id,
            [OVERALL_LOAD_USERS[12].user_id, OVERALL_LOAD_USERS[13].user_id],
            [3, 9],
        ),
        (
            OVERALL_LOAD_JOBS[4].job_id,
            [
                OVERALL_LOAD_USERS[12].user_id,
                OVERALL_LOAD_USERS[13].user_id,
                OVERALL_LOAD_USERS[14].user_id,
            ],
            [2, 8, 2],
        ),
    ],
)
def test_overall_load_recalculation_when_add_users(
    monkeypatch,
    prepare_db_for_overall_load,
    job_id,
    users,
    expected_overall_load,
):
    """Tests overall load recalculation for job with auto_distribution
    when adding or deleting users"""
    session = prepare_db_for_overall_load
    monkeypatch.setattr(
        "app.jobs.services.get_job_names",
        Mock(return_value={job_id: "JobName"}),
    )
    response = client.patch(
        f"jobs/{job_id}",
        json={"annotators": users},
        headers=TEST_HEADERS,
    )
    users_overall_load = (
        session.query(User.overall_load)
        .filter(User.user_id.in_(users))
        .order_by(User.user_id)
        .all()
    )
    users_overall_load = [user[0] for user in users_overall_load]
    assert users_overall_load == expected_overall_load
    assert response.status_code == 204


@mark.integration
@mark.parametrize(
    [
        "job_id",
        "users",
        "expected_overall_load",
        "first_user_overall_load_expected",
    ],
    [
        (
            OVERALL_LOAD_JOBS[4].job_id,
            [OVERALL_LOAD_USERS[12].user_id],
            [12],
            12,
        ),
        (
            OVERALL_LOAD_JOBS[4].job_id,
            [OVERALL_LOAD_USERS[13].user_id, OVERALL_LOAD_USERS[14].user_id],
            [3, 3],
            6,
        ),
    ],
)
def test_overall_load_recalculation_when_delete_users(
    monkeypatch,
    prepare_db_for_overall_load,
    job_id,
    users,
    expected_overall_load,
    first_user_overall_load_expected,
):
    session = prepare_db_for_overall_load
    monkeypatch.setattr(
        "app.jobs.services.get_job_names",
        Mock(return_value={job_id: "JobName"}),
    )
    response = client.patch(
        f"jobs/{job_id}",
        json={
            "annotators": users,
            "validators": [OVERALL_LOAD_USERS[12].user_id],
        },
        headers=TEST_HEADERS,
    )
    users_overall_load = (
        session.query(User.overall_load).filter(User.user_id.in_(users)).all()
    )
    first_user_overall_load_db = (
        session.query(User.overall_load)
        .filter(User.user_id == OVERALL_LOAD_USERS[12].user_id)
        .scalar()
    )
    users_overall_load = [user[0] for user in users_overall_load]
    assert first_user_overall_load_db == first_user_overall_load_expected
    assert users_overall_load == expected_overall_load
    assert response.status_code == 204
