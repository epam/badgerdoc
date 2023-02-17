import re
from datetime import datetime, timedelta
from typing import Any, List, Optional
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
import responses
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
)
from annotation.microservice_communication.jobs_communication import (
    JOBS_SEARCH_URL,
)
from annotation.microservice_communication.user import USERS_SEARCH_URL
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import CategoryTypeSchema, ValidationSchema
from tests.consts import CRUD_TASKS_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app
from tests.test_post import check_files_distributed_pages

client = TestClient(app)

CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]
ANNOTATORS = (
    User(user_id="49807ec8-ec18-40a3-8e44-2e9462c00413"),
    User(
        user_id="72b31ea3-fde2-4c7a-82b7-c27874b81217",
        default_load=10,
    ),
    User(user_id="5c9a1d6f-63ab-4777-bc1c-53984a5c9105"),
    User(user_id="9eace50e-613e-4352-b287-85fd91c88b51"),
)
SEARCH_TASKS_PATH = CRUD_TASKS_PATH + "/search"
CRUD_CR_JOBS = (
    Job(
        job_id=1,
        name="annotation_job_1",
        callback_url="http://www.test.com",
        annotators=[
            ANNOTATORS[0],
            ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=2,
        name="annotation_job_2",
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[0]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=3,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=4,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[2], ANNOTATORS[3]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-30T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=5,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[0], ANNOTATORS[1], ANNOTATORS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=6,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[0], ANNOTATORS[1], ANNOTATORS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=7,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[0], ANNOTATORS[1], ANNOTATORS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant="other_tenant",
    ),
    Job(
        job_id=8,
        callback_url="http://www.test.com",
        annotators=[],
        validators=[ANNOTATORS[0], ANNOTATORS[2]],
        owners=[],
        validation_type=ValidationSchema.validation_only,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=9,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[0], ANNOTATORS[2]],
        validators=[ANNOTATORS[1], ANNOTATORS[2]],
        owners=[],
        validation_type=ValidationSchema.hierarchical,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=10,
        callback_url="http://www.test.com",
        annotators=[],
        validators=[],
        owners=[],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),  # ExtractionJob
)
FILES_IDS = (
    1,
    2,
    3,
    4,
    5,
)
FILES = (
    File(
        file_id=FILES_IDS[0],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[0].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[1],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[0].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[2],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[0].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[2],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[1].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[3],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[1].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[3],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[3].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[4],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[5].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[4],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[7].job_id,
        pages_number=20,
        distributed_annotating_pages=list(range(1, 21)),
        annotated_pages=list(range(1, 21)),
    ),
    File(
        file_id=FILES_IDS[1],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[4].job_id,
        pages_number=100,
    ),
    File(
        file_id=FILES_IDS[2],
        tenant=TEST_TENANT,
        job_id=CRUD_CR_JOBS[3].job_id,
        pages_number=100,
    ),
)

CRUD_CR_ANNOTATION_TASKS = (
    ManualAnnotationTask(
        file_id=FILES[0].file_id,
        is_validation=False,
        job_id=CRUD_CR_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        status="Pending",
        user_id=ANNOTATORS[0].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        file_id=FILES[1].file_id,
        is_validation=False,
        job_id=CRUD_CR_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        status="Pending",
        user_id=ANNOTATORS[1].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        file_id=FILES[2].file_id,
        is_validation=False,
        job_id=CRUD_CR_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Pending",
        user_id=ANNOTATORS[3].user_id,
        deadline="2021-11-19T01:01:01",
    ),
    ManualAnnotationTask(
        file_id=FILES[3].file_id,
        is_validation=False,
        job_id=CRUD_CR_JOBS[1].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Pending",
        user_id=ANNOTATORS[3].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        file_id=FILES[3].file_id,
        is_validation=True,
        job_id=CRUD_CR_JOBS[1].job_id,
        pages=[1, 2, 3, 4, 5],
        status="in_progress",
        user_id=ANNOTATORS[3].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        file_id=FILES[3].file_id,
        is_validation=True,
        job_id=CRUD_CR_JOBS[1].job_id,
        pages=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="ready",
        user_id=ANNOTATORS[3].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        file_id=FILES[0].file_id,
        is_validation=True,
        job_id=CRUD_CR_JOBS[6].job_id,
        pages=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="ready",
        user_id=ANNOTATORS[0].user_id,
        deadline="2021-10-19T01:01:01",
    ),
    *[
        ManualAnnotationTask(
            file_id=FILES[4].file_id,
            is_validation=False,
            job_id=CRUD_CR_JOBS[5].job_id,
            pages=[1, 2, 3, 4, 5],
            status="Pending",
            user_id=ANNOTATORS[0].user_id,
            deadline="2021-10-19T01:01:02",
        )
        for _ in range(10)
    ],
)
TASKS_WRONG_PAGES = [
    {
        "file_id": FILES_IDS[3],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[3].job_id,
        "pages": [-1, -3, 1, 2, 3],
        "status": "Pending",
        "user_id": ANNOTATORS[2].user_id,
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[3],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[3].job_id,
        "pages": [0, 1],
        "status": "Pending",
        "user_id": ANNOTATORS[2].user_id,
        "deadline": "2021-10-19T01:01:01",
    },
]
TASK_WRONG_JOB = {
    "file_id": FILES_IDS[0],
    "is_validation": False,
    "job_id": 11,
    "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    "status": "Pending",
    "user_id": ANNOTATORS[0].user_id,
    "deadline": "2021-10-19T01:01:01",
}
NEW_TASKS = (
    {
        "file_id": FILES_IDS[1],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[4].job_id,
        "pages": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
        "user_id": ANNOTATORS[2].user_id,
        "deadline": "2021-12-12T01:01:01",
    },
    {
        "file_id": FILES_IDS[2],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[3].job_id,
        "pages": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
        "user_id": ANNOTATORS[2].user_id,
        "deadline": None,
    },
    {
        "file_id": FILES_IDS[3],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[4].job_id,
        "pages": [31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
        "user_id": "a986b1ef-1fe2-450f-9e66-16623dcd8c22",
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[2],
        "is_validation": True,
        "job_id": CRUD_CR_JOBS[3].job_id,
        "pages": [51, 52, 53],
        "user_id": ANNOTATORS[2].user_id,
        "deadline": None,
    },
    {
        "file_id": FILES_IDS[4],
        "is_validation": True,
        "job_id": CRUD_CR_JOBS[7].job_id,
        "pages": [1, 2, 3],
        "user_id": ANNOTATORS[2].user_id,
        "deadline": None,
    },
    {
        "file_id": FILES_IDS[3],
        "is_validation": True,
        "job_id": CRUD_CR_JOBS[4].job_id,
        "pages": [31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
        "user_id": "a986b1ef-1fe2-450f-9e66-16623dcd8c22",
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[0],
        "is_validation": True,
        "job_id": CRUD_CR_JOBS[0].job_id,
        "pages": [1, 2, 3, 20, 21, 22],
        "user_id": ANNOTATORS[0].user_id,
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[0],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[8].job_id,
        "pages": [1, 2, 3, 20, 21, 22],
        "user_id": ANNOTATORS[1].user_id,
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[0],
        "is_validation": True,
        "job_id": CRUD_CR_JOBS[8].job_id,
        "pages": [1, 2, 3, 20, 21, 22],
        "user_id": ANNOTATORS[0].user_id,
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[0],
        "is_validation": True,
        "job_id": CRUD_CR_JOBS[1].job_id,
        "pages": [1, 2, 3, 20, 21, 22],
        "user_id": ANNOTATORS[0].user_id,
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[3],
        "is_validation": True,
        "job_id": CRUD_CR_JOBS[0].job_id,
        "pages": [1, 2, 3, 20, 21, 22],
        "user_id": ANNOTATORS[0].user_id,
        "deadline": "2021-10-19T01:01:01",
    },
    {
        "file_id": FILES_IDS[1],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[4].job_id,
        "pages": [99, 100, 101, 102],
        "user_id": ANNOTATORS[2].user_id,
        "deadline": "2021-12-12T01:01:01",
    },
    {
        "file_id": FILES_IDS[1],
        "is_validation": False,
        "job_id": CRUD_CR_JOBS[9].job_id,
        "pages": [99, 100, 101, 102],
        "user_id": ANNOTATORS[2].user_id,
        "deadline": "2021-12-12T01:01:01",
    },
)
ASSET_FILE_RESPONSE = {
    "pagination": {
        "page_num": 1,
        "page_size": 15,
        "min_pages_left": 1,
        "total": 3,
        "has_more": False,
    },
    "data": [
        {
            "id": 1,
            "original_name": "1.pdf",
        },
        {
            "id": 2,
            "original_name": "2.pdf",
        },
        {
            "id": 3,
            "original_name": "3.pdf",
        },
    ],
}
JOBS_RESPONSE = {
    "pagination": {
        "page_num": 1,
        "page_size": 15,
        "min_pages_left": 1,
        "total": 2,
        "has_more": False,
    },
    "data": [
        {
            "id": 1,
            "name": "annotation_job_1",
        },
        {
            "id": 2,
            "name": "annotation_job_2",
        },
    ],
}
EXPANDED_TASKS_RESPONSE = [
    dict(
        is_validation=False,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        status="Pending",
        user={"id": ANNOTATORS[0].user_id, "name": "admin"},
        deadline="2021-10-19T01:01:01",
        file={
            "id": FILES[0].file_id,
            "name": ASSET_FILE_RESPONSE["data"][0]["original_name"],
        },
        job={
            "id": CRUD_CR_JOBS[0].job_id,
            "name": "annotation_job_1",
        },
    ),
    dict(
        is_validation=False,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        status="Pending",
        user={"id": ANNOTATORS[1].user_id, "name": "admin"},
        deadline="2021-10-19T01:01:01",
        file={
            "id": FILES[1].file_id,
            "name": ASSET_FILE_RESPONSE["data"][1]["original_name"],
        },
        job={
            "id": CRUD_CR_JOBS[0].job_id,
            "name": "annotation_job_1",
        },
    ),
    dict(
        is_validation=False,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Pending",
        user={"id": ANNOTATORS[3].user_id, "name": "admin"},
        deadline="2021-11-19T01:01:01",
        file={
            "id": FILES[2].file_id,
            "name": ASSET_FILE_RESPONSE["data"][2]["original_name"],
        },
        job={
            "id": CRUD_CR_JOBS[0].job_id,
            "name": "annotation_job_1",
        },
    ),
    dict(
        is_validation=False,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Pending",
        user={"id": ANNOTATORS[3].user_id, "name": "admin"},
        deadline="2021-10-19T01:01:01",
        file={
            "id": FILES[3].file_id,
            "name": ASSET_FILE_RESPONSE["data"][2]["original_name"],
        },
        job={
            "id": CRUD_CR_JOBS[1].job_id,
            "name": "annotation_job_2",
        },
    ),
    dict(
        is_validation=True,
        pages=[1, 2, 3, 4, 5],
        status="In Progress",
        user={"id": ANNOTATORS[3].user_id, "name": "admin"},
        deadline="2021-10-19T01:01:01",
        file={
            "id": FILES[3].file_id,
            "name": ASSET_FILE_RESPONSE["data"][2]["original_name"],
        },
        job={
            "id": CRUD_CR_JOBS[1].job_id,
            "name": "annotation_job_2",
        },
    ),
    dict(
        is_validation=True,
        pages=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Ready",
        user={"id": ANNOTATORS[3].user_id, "name": "admin"},
        deadline="2021-10-19T01:01:01",
        file={
            "id": FILES[3].file_id,
            "name": ASSET_FILE_RESPONSE["data"][2]["original_name"],
        },
        job={
            "id": CRUD_CR_JOBS[1].job_id,
            "name": "annotation_job_2",
        },
    ),
]
USERS_SEARCH_RESPONSE = {
    "access": {
        "manageGroupMembership": True,
        "view": True,
        "mapRoles": True,
        "impersonate": True,
        "manage": True,
    },
    "attributes": {"tenants": ["test"]},
    "clientConsents": None,
    "clientRoles": None,
    "createdTimestamp": 1638362379072,
    "credentials": None,
    "disableableCredentialTypes": [],
    "email": None,
    "emailVerified": False,
    "enabled": True,
    "federatedIdentities": [],
    "federationLink": None,
    "firstName": None,
    "groups": None,
    "id": "02336646-f5d0-4670-b111-c140a3ad58b5",
    "lastName": None,
    "notBefore": 0,
    "origin": None,
    "realmRoles": None,
    "requiredActions": [],
    "self": None,
    "serviceAccountClientId": None,
    "username": "admin",
}


def prepare_task_stats_expected_response(
    task_id: int,
    event_type: str = "opened",
    additional_data: Optional[dict] = None,
    created: Optional[str] = None,
    updated: Optional[str] = None,
) -> dict:
    return {
        "event_type": event_type,
        "additional_data": additional_data,
        "task_id": task_id,
    }


def validate_datetime(reponse_content: dict, is_updated: bool = False) -> bool:
    created = reponse_content["created"]
    updated = reponse_content["updated"]
    if (
        not created
        or (updated and not created)
        or (is_updated and not updated)
        or (not is_updated and updated)
    ):
        return False

    for field in [created, updated]:
        if not field:
            continue
        timestamp = datetime.fromisoformat(field)
        if datetime.utcnow() - timestamp > timedelta(minutes=5):
            return False
    return True


def prepare_stats_export_body(
    user_ids: List[str],
    date_from: Optional[datetime] = datetime.now() - timedelta(days=365),
    date_to: Optional[datetime] = datetime.now() + timedelta(days=365),
) -> dict:
    return {
        "user_ids": user_ids,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }


@pytest.mark.integration
@patch.object(Session, "query")
def test_post_task_500_response(Session, prepare_db_for_cr_task):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.post(
        CRUD_TASKS_PATH, json=NEW_TASKS[0], headers=TEST_HEADERS
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
def test_post_task_wrong_job(prepare_db_for_cr_task):
    response = client.post(
        CRUD_TASKS_PATH, json=TASK_WRONG_JOB, headers=TEST_HEADERS
    )
    assert response.status_code == 400
    assert "Error: wrong job_id" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_info", "error_message"],
    [
        (
            NEW_TASKS[2],
            f"{NEW_TASKS[2]['user_id']} is not assigned as annotator",
        ),  # cross job annotation - user not in job annotators
        (
            NEW_TASKS[5],
            f"{NEW_TASKS[5]['user_id']} is not assigned as validator",
        ),  # cross job validation - user not in job annotators
        (
            NEW_TASKS[6],
            "file's pages that are already distributed in annotation "
            "tasks for this user: {1, 2, 3}",
        ),  # cross job validation - user annotating some of the same pages
        (
            NEW_TASKS[7],
            f"{NEW_TASKS[7]['user_id']} is not assigned as annotator",
        ),  # hierarchical job annotation - user not in job annotators
        (
            NEW_TASKS[8],
            f"{NEW_TASKS[8]['user_id']} is not assigned as validator",
        ),  # hierarchical job annotation - user not in job validators
        (
            NEW_TASKS[12],
            f"{NEW_TASKS[12]['user_id']} is not assigned",
        ),  # ExtractionJob
    ],
)
def test_post_task_wrong_users_errors(
    prepare_db_for_cr_task, task_info, error_message
):
    response = client.post(
        CRUD_TASKS_PATH, json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == 400
    assert error_message in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    "task_info",
    [
        TASKS_WRONG_PAGES[0],
        TASKS_WRONG_PAGES[1],
    ],
)
def test_post_task_422_pages_response(prepare_db_for_cr_task, task_info):
    response = client.post(
        CRUD_TASKS_PATH, json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_info", "expected_response"],
    [
        (
            NEW_TASKS[0],
            {**NEW_TASKS[0], "status": "Pending"},
        ),
        (
            NEW_TASKS[1],
            {
                **NEW_TASKS[1],
                "status": "Pending",
                "deadline": CRUD_CR_JOBS[3].deadline,
            },
        ),
        (
            NEW_TASKS[3],
            {
                **NEW_TASKS[3],
                "status": "Pending",
                "deadline": CRUD_CR_JOBS[3].deadline,
            },
        ),
    ],
)
def test_post_task(prepare_db_for_cr_task, task_info, expected_response):
    response = client.post(
        CRUD_TASKS_PATH, json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == 201
    assert [
        value
        for key, value in response.json().items()
        if key == "id" and value
    ]
    response = {
        key: value for key, value in response.json().items() if key != "id"
    }
    assert response == expected_response
    check_files_distributed_pages(prepare_db_for_cr_task, task_info["job_id"])


@pytest.mark.integration
def test_add_task_stats_start_from_close(prepare_db_for_cr_task):
    response = client.post(
        f"{CRUD_TASKS_PATH}/{CRUD_CR_ANNOTATION_TASKS[0].id}/stats",
        json={"event_type": "closed"},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 400
    assert "Field constraint error." in response.text


@pytest.mark.integration
def test_add_task_stats_404_not_found(prepare_db_for_cr_task):
    id_ = uuid4().int

    response = client.post(
        f"{CRUD_TASKS_PATH}/{id_}/stats",
        json={"event_type": "opened"},
        headers=TEST_HEADERS,
    )

    assert response.status_code == 404
    assert f"Task with id {id_} not found." in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id"],
    # Task ids
    [(id_,) for id_ in [1, 2, 3, 4, 5]],
)
def test_create_task_stats(prepare_db_for_cr_task, task_id):
    response = client.post(
        f"{CRUD_TASKS_PATH}/{task_id}/stats",
        json={"event_type": "opened"},
        headers=TEST_HEADERS,
    )
    content = response.json()

    assert response.status_code == 201
    assert validate_datetime(content, is_updated=False)
    assert prepare_task_stats_expected_response(
        task_id=task_id
    ) == prepare_task_stats_expected_response(**content)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id"],
    # Task ids
    [(id_,) for id_ in [1, 2, 3, 4, 5]],
)
def test_update_task_stats_same_event(prepare_db_update_stats, task_id):
    response = client.post(
        f"{CRUD_TASKS_PATH}/{task_id}/stats",
        json={"event_type": "opened"},
        headers=TEST_HEADERS,
    )
    content = response.json()

    assert response.status_code == 201
    assert validate_datetime(content, is_updated=True)
    assert prepare_task_stats_expected_response(
        task_id=task_id
    ) == prepare_task_stats_expected_response(**content)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id"],
    # Task ids
    [(id_,) for id_ in [1, 2, 3, 4, 5]],
)
def test_update_task_already_updated(
    prepare_db_update_stats_already_updated,
    task_id,
):
    response = client.post(
        f"{CRUD_TASKS_PATH}/{task_id}/stats",
        json={"event_type": "opened"},
        headers=TEST_HEADERS,
    )
    content = response.json()

    assert response.status_code == 201
    assert validate_datetime(content, is_updated=True)
    assert prepare_task_stats_expected_response(
        task_id=task_id
    ) == prepare_task_stats_expected_response(**content)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id"],
    # Task ids
    [(id_,) for id_ in [1, 2, 3, 4, 5]],
)
def test_update_task_already_updated_change_event(
    prepare_db_update_stats_already_updated,
    task_id,
):
    response = client.post(
        f"{CRUD_TASKS_PATH}/{task_id}/stats",
        json={"event_type": "closed"},
        headers=TEST_HEADERS,
    )
    content = response.json()

    assert response.status_code == 201
    assert validate_datetime(content, is_updated=True)
    assert prepare_task_stats_expected_response(
        task_id=task_id,
        event_type="closed",
    ) == prepare_task_stats_expected_response(**content)


@pytest.mark.integration
def test_create_export_data_not_found(prepare_db_update_stats):
    body = prepare_stats_export_body(
        user_ids=[f"{uuid4()}" for _ in range(10)]
    )

    response = client.post(
        f"{CRUD_TASKS_PATH}/export",
        json=body,
        headers=TEST_HEADERS,
    )

    assert response.status_code == 406
    assert "Export data not found." in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["date_from", "date_to"],
    [
        ("2021-12-15", "2100-12-15T00:00:00"),
        ("abcdef", "2100-12-15T00:00:00"),
        ("2000-12-15T00:00:00", "!@#$%^"),
        ("2000-12-15T00:00:00", "2100-12-15"),
    ],
)
def test_create_export_invalid_datetime_format(
    prepare_db_for_cr_task, date_from, date_to
):
    body = prepare_stats_export_body(
        user_ids=[f"{uuid4()}" for _ in range(10)]
    )
    body["date_from"] = date_from
    body["date_to"] = date_to

    response = client.post(
        f"{CRUD_TASKS_PATH}/export",
        json=body,
        headers=TEST_HEADERS,
    )

    assert response.status_code == 422
    assert "invalid datetime format" in response.text


@pytest.mark.integration
def test_create_export_return_csv(prepare_db_update_stats_already_updated):
    body = prepare_stats_export_body(
        user_ids=[str(ann.user_id) for ann in ANNOTATORS]
    )

    response = client.post(
        f"{CRUD_TASKS_PATH}/export",
        json=body,
        headers=TEST_HEADERS,
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert (
        "filename=annotator_stats_export"
        in response.headers["content-disposition"]
    )
    assert len(response.content) > 0


@pytest.mark.unittest
@patch.object(Session, "query")
def test_get_task_500_response(Session):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(CRUD_TASKS_PATH + "/1", headers=TEST_HEADERS)
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
def test_get_task_404_response(prepare_db_for_cr_task):
    response = client.get(CRUD_TASKS_PATH + "/111", headers=TEST_HEADERS)
    assert response.status_code == 404
    assert "Task with id" in response.text


@pytest.mark.integration
@responses.activate
def test_get_task(prepare_db_for_cr_task):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSET_FILE_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.GET,
        re.compile(f"{USERS_SEARCH_URL}/\\w+"),
        json=USERS_SEARCH_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    response = client.get(
        "{0}/{1}".format(CRUD_TASKS_PATH, CRUD_CR_ANNOTATION_TASKS[3].id),
        headers=TEST_HEADERS,
    )
    assert response.status_code == 200
    response = response.json()
    del response["id"]
    assert response == EXPANDED_TASKS_RESPONSE[3]


@pytest.mark.unittest
@patch.object(Session, "query")
def test_get_tasks_500_response(Session):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(CRUD_TASKS_PATH, params={}, headers=TEST_HEADERS)
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
def test_get_tasks_404_response(prepare_db_for_cr_task):
    response = client.get(
        CRUD_TASKS_PATH, params={"file_id": 111}, headers=TEST_HEADERS
    )
    assert response.status_code == 404
    assert "Tasks with parameters" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["url_params", "expected_annotation_tasks"],
    [
        (
            {"file_id": 1},
            [EXPANDED_TASKS_RESPONSE[0]],
        ),
        (
            {"job_id": 1},
            EXPANDED_TASKS_RESPONSE[:3],
        ),
        (
            {
                "job_id": 1,
                "user_id": "9eace50e-613e-4352-b287-85fd91c88b51",
            },
            [EXPANDED_TASKS_RESPONSE[2]],
        ),
        (
            {"user_id": "72b31ea3-fde2-4c7a-82b7-c27874b81217"},
            [EXPANDED_TASKS_RESPONSE[1]],
        ),
        (
            {
                "job_id": 1,
                "deadline": "2021-11-19T01:01:01",
            },
            [EXPANDED_TASKS_RESPONSE[2]],
        ),
        (
            {"job_id": 1, "task_status": "Pending"},
            EXPANDED_TASKS_RESPONSE[:3],
        ),
        (
            {"job_id": 2, "task_status": "Ready"},
            [EXPANDED_TASKS_RESPONSE[5]],
        ),
        (
            {"job_id": 2, "task_status": "In Progress"},
            [EXPANDED_TASKS_RESPONSE[4]],
        ),
    ],
)
@responses.activate
def test_get_tasks(
    prepare_db_for_cr_task,
    url_params: dict,
    expected_annotation_tasks: dict,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSET_FILE_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.POST,
        JOBS_SEARCH_URL,
        json={1: "annotation_job_1"},
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.GET,
        re.compile(f"{USERS_SEARCH_URL}/\\w+"),
        json=USERS_SEARCH_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    response = client.get(
        CRUD_TASKS_PATH, params=url_params, headers=TEST_HEADERS
    )
    assert response.status_code == 200
    response = [
        {key: value for key, value in x.items() if key != "id"}
        for x in response.json()["annotation_tasks"]
    ]
    assert response == expected_annotation_tasks


@pytest.mark.integration
@pytest.mark.parametrize(
    ["url_params", "expected_response"],
    [
        (
            {
                "job_id": 1,
                "pagination_page_size": 1,
                "pagination_start_page": 1,
            },
            {
                "current_page": 1,
                "page_size": 1,
                "total_objects": 3,
            },
        ),
        (
            {
                "job_id": 1,
                "pagination_page_size": 1,
                "pagination_start_page": 2,
            },
            {
                "current_page": 2,
                "page_size": 1,
                "total_objects": 3,
            },
        ),
        (
            {
                "job_id": 1,
                "pagination_page_size": 1,
                "pagination_start_page": 3,
            },
            {
                "current_page": 3,
                "page_size": 1,
                "total_objects": 3,
            },
        ),
        (
            {
                "job_id": 1,
                "pagination_page_size": 2,
                "pagination_start_page": 1,
            },
            {
                "current_page": 1,
                "page_size": 2,
                "total_objects": 3,
            },
        ),
        (
            {
                "job_id": 1,
                "pagination_page_size": 2,
                "pagination_start_page": 2,
            },
            {
                "current_page": 2,
                "page_size": 2,
                "total_objects": 3,
            },
        ),
    ],
)
@responses.activate
def test_get_tasks_pagination(
    prepare_db_for_cr_task,
    url_params: dict,
    expected_response: dict,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSET_FILE_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.POST,
        JOBS_SEARCH_URL,
        json=JOBS_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.GET,
        re.compile(f"{USERS_SEARCH_URL}/\\w+"),
        json=USERS_SEARCH_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    response = client.get(
        CRUD_TASKS_PATH, params=url_params, headers=TEST_HEADERS
    )
    assert response.status_code == 200
    response = {
        key: value
        for key, value in response.json().items()
        if key != "annotation_tasks"
    }
    assert response == expected_response


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_info", "expected_deadline"],
    [
        (NEW_TASKS[0], NEW_TASKS[0]["deadline"]),
        (NEW_TASKS[1], CRUD_CR_JOBS[3].deadline),
        (NEW_TASKS[3], CRUD_CR_JOBS[3].deadline),
    ],
)
def test_post_task_deadline(
    prepare_db_for_cr_task, task_info, expected_deadline
):
    response = client.post(
        CRUD_TASKS_PATH, json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == 201
    assert response.json()["deadline"] == expected_deadline
    check_files_distributed_pages(prepare_db_for_cr_task, task_info["job_id"])


def prepare_filtration_body(
    page_num: Optional[int] = 1,
    page_size: Optional[int] = 15,
    filter_field: Optional[str] = "id",
    operator: Optional[str] = "eq",
    value: Optional[Any] = 1,
    ordering_field: Optional[str] = "id",
    direction: Optional[str] = "asc",
    no_filtration: Optional[bool] = False,
) -> dict:
    body = {
        "pagination": {
            "page_num": page_num,
            "page_size": page_size,
        },
        "filters": [
            {
                "field": filter_field,
                "operator": operator,
                "value": value,
            }
        ],
        "sorting": [
            {
                "field": ordering_field,
                "direction": direction,
            }
        ],
    }
    if no_filtration:
        body.pop("filters")
    return body


def prepare_filtration_body_double_filter(
    page_num: Optional[int] = 1,
    page_size: Optional[int] = 15,
    first_field: Optional[str] = "user_id",
    second_field: Optional[str] = "status",
    sorting_field: Optional[str] = "status",
    first_operator: Optional[str] = "distinct",
    second_operator: Optional[str] = "distinct",
    value: Optional[Any] = "string",
    direction: Optional[str] = "asc",
    no_filtration: Optional[bool] = False,
) -> dict:
    body = {
        "pagination": {
            "page_num": page_num,
            "page_size": page_size,
        },
        "filters": [
            {
                "field": first_field,
                "operator": first_operator,
                "value": value,
            },
            {
                "field": second_field,
                "operator": second_operator,
                "value": value,
            },
        ],
        "sorting": [
            {
                "field": sorting_field,
                "direction": direction,
            }
        ],
    }
    if no_filtration:
        body.pop("filters")
    return body


@pytest.mark.integration
@patch(
    "annotation.tasks.resources.filter_tasks_db", side_effect=SQLAlchemyError
)
def test_search_tasks_500_error(prepare_db_for_cr_task):
    data = prepare_filtration_body()
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@pytest.mark.integration
def test_search_tasks_400_error(prepare_db_for_cr_task):
    data = prepare_filtration_body(
        ordering_field="status", operator="distinct"
    )
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    error_message = (
        "SELECT DISTINCT ON expressions must "
        "match initial ORDER BY expressions"
    )
    assert response.status_code == 400
    assert error_message in response.text


@pytest.mark.integration
def test_search_two_filters_different_distinct_order(prepare_db_for_cr_task):
    data = prepare_filtration_body_double_filter(
        first_field="status",
        second_field="user_id",
        second_operator="is_not_null",
        sorting_field="status",
    )
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    first_result_data = response.json()["data"]
    data = prepare_filtration_body_double_filter(first_operator="is_not_null")
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    second_result_data = response.json()["data"]
    assert first_result_data == second_result_data


@pytest.mark.integration
def test_search_two_filters_both_distinct(prepare_db_for_cr_task):
    data = prepare_filtration_body_double_filter()
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    result_data = response.json()["data"]
    assert response.status_code == 200
    assert len(result_data) == 6


@pytest.mark.integration
@pytest.mark.parametrize(
    ["page_num", "page_size", "result_length"],
    [(1, 15, 15), (2, 15, 7), (3, 15, 0), (22, 30, 0)],
)
@responses.activate
def test_search_tasks_pagination(
    page_num, page_size, result_length, prepare_db_for_cr_task
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSET_FILE_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.POST,
        JOBS_SEARCH_URL,
        json=JOBS_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.GET,
        re.compile(f"{USERS_SEARCH_URL}/\\w+"),
        json=USERS_SEARCH_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    data = prepare_filtration_body(
        page_num=page_num, page_size=page_size, no_filtration=True
    )
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    tasks = response.json()["data"]
    pagination = response.json()["pagination"]
    assert response.status_code == 200
    assert pagination["total"] == 22
    assert pagination["page_num"] == page_num
    assert pagination["page_size"] == page_size
    assert len(tasks) == result_length


@pytest.mark.integration
@pytest.mark.parametrize(
    ["filter_field", "operator", "value", "expected_ids"],
    [
        ("id", "eq", 1, [1]),
        ("id", "lt", 10, [*range(1, 7), 8, 9]),  # Without other tenant's task
        ("id", "ge", 15, list(range(15, 24))),
        ("job_id", "eq", 7, []),  # Other tenant's job_id
        (
            "user_id",
            "eq",
            "9eace50e-613e-4352-b287-85fd91c88b51",
            list(range(3, 7)),
        ),
        ("is_validation", "ne", False, [5, 6, 20, 23]),
        ("is_validation", "ne", False, [5, 6, 20, 23]),
        ("status", "not_in", ["pending", "ready"], [5]),
        ("file_id", "in", [1, 2], [1, 2, 18, 21]),
        ("deadline", "gt", "2021-10-19T01:01:01", [3, *range(8, 24)]),
        ("id", "distinct", "string", [*range(1, 7), *range(8, 24)]),
    ],
)
@responses.activate
def tests_search_tasks_filtration(
    filter_field, operator, value, expected_ids, prepare_db_for_cr_task
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSET_FILE_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.POST,
        JOBS_SEARCH_URL,
        json=JOBS_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.GET,
        re.compile(f"{USERS_SEARCH_URL}/\\w+"),
        json=USERS_SEARCH_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    data = prepare_filtration_body(
        filter_field=filter_field,
        operator=operator,
        value=value,
        page_size=30,
    )
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 200
    if operator == "distinct":
        assert response.json()["data"] == expected_ids
    else:
        tasks = response.json()["data"]
        result_ids_order = [task["id"] for task in tasks]
        assert result_ids_order == expected_ids


@pytest.mark.integration
@pytest.mark.parametrize(
    ["ordering_field", "direction", "expected_order_ids"],
    [
        ("id", "asc", [4, 5, 6]),
        ("id", "desc", [6, 5, 4]),
        ("status", "asc", [4, 6, 5]),
    ],
)
@responses.activate
def tests_search_tasks_ordering(
    ordering_field, direction, expected_order_ids, prepare_db_for_cr_task
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSET_FILE_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    responses.add(
        responses.GET,
        re.compile(f"{USERS_SEARCH_URL}/\\w+"),
        json=USERS_SEARCH_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    data = prepare_filtration_body(
        filter_field="job_id",
        value=2,
        ordering_field=ordering_field,
        direction=direction,
    )
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    tasks = response.json()["data"]
    result_ids_order = [task["id"] for task in tasks]
    assert response.status_code == 200
    assert result_ids_order == expected_order_ids


@pytest.mark.integration
@pytest.mark.parametrize(
    ["wrong_parameter", "value"],
    [
        ("filter_field", "wrong_field"),
        ("operator", "wrong_operator"),
        ("page_size", 0),
    ],
)
@responses.activate
def test_search_tasks_wrong_parameters(
    wrong_parameter, value, prepare_db_for_cr_task
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSET_FILE_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    data = prepare_filtration_body(**{wrong_parameter: value})
    response = client.post(SEARCH_TASKS_PATH, json=data, headers=TEST_HEADERS)
    assert response.status_code == 422
    assert "value is not a valid enumeration member" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_info", "expected_status_code", "expected_response"],
    [
        (
            NEW_TASKS[4],
            201,
            {
                **NEW_TASKS[4],
                "status": "Pending",
                "deadline": CRUD_CR_JOBS[7].deadline,
            },
        ),
        (
            {**NEW_TASKS[4], "is_validation": False},
            400,
            {"detail": "Error: this job is validation only."},
        ),
    ],
)
def test_post_task_validation_only(
    prepare_db_for_cr_task, task_info, expected_status_code, expected_response
):
    response = client.post(
        CRUD_TASKS_PATH, json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == expected_status_code
    response = (
        {key: value for key, value in response.json().items() if key != "id"}
        if response.status_code == 201
        else response.json()
    )
    assert response == expected_response
    check_files_distributed_pages(prepare_db_for_cr_task, task_info["job_id"])


@pytest.mark.integration
@pytest.mark.parametrize("task_info", (NEW_TASKS[9], NEW_TASKS[10]))
def test_post_task_wrong_file_error(prepare_db_for_cr_task, task_info):
    response = client.post(
        CRUD_TASKS_PATH, json=task_info, headers=TEST_HEADERS
    )
    error_message = (
        f"{task_info['file_id']} is not assigned for job {task_info['job_id']}"
    )
    assert response.status_code == 400
    assert error_message in response.text


@pytest.mark.integration
def test_post_task_wrong_file_pages(prepare_db_for_cr_task):
    response = client.post(
        CRUD_TASKS_PATH, json=NEW_TASKS[11], headers=TEST_HEADERS
    )
    error_message = "({101, 102}) do not belong to file %s" % (
        NEW_TASKS[11]["file_id"]
    )
    assert response.status_code == 400
    assert error_message in response.text
