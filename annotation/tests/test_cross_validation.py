from copy import copy
from uuid import UUID

import pytest
from tests.test_distribution import JOB_ID

from annotation.distribution import (distribute_validation_partial_files,
                                     distribute_whole_files)
from annotation.errors import FieldConstraintError
from annotation.jobs import check_annotators, check_validators
from annotation.schemas import TaskStatusEnumSchema, ValidationSchema

TASKS_STATUS = TaskStatusEnumSchema.pending
VALIDATION_TYPE = ValidationSchema.cross


@pytest.mark.unittest
def test_cross_single_user_error():
    message = (
        "There must be more than one annotator provided for cross validation "
        "job tasks creation"
    )
    with pytest.raises(FieldConstraintError, match=message):
        check_annotators({UUID(USERS[0]["user_id"])}, VALIDATION_TYPE)


@pytest.mark.unittest
def test_cross_with_validators_error():
    message = (
        "If the validation type is cross validation, no validators should "
        "be provided."
    )
    with pytest.raises(FieldConstraintError, match=message):
        check_validators(
            {UUID(USERS[0]["user_id"])},
            VALIDATION_TYPE,
        )


FILES_EQUAL = [
    {
        "file_id": 1,
        "pages_number": 9,
    },
    {
        "file_id": 2,
        "pages_number": 12,
    },
    {
        "file_id": 3,
        "pages_number": 2,
    },
    {
        "file_id": 4,
        "pages_number": 4,
    },
    {
        "file_id": 5,
        "pages_number": 4,
    },
]

USERS = [
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d991",
        "pages_number": 0,
    },
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d992",
        "pages_number": 0,
    },
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d991",
        "pages_number": 12,
    },
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d992",
        "pages_number": 9,
    },
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d991",
        "pages_number": 60,
    },
]

ANNOTATED_FILES_PAGES = [
    {USERS[0]["user_id"]: [{"file_id": 1, "pages": list(range(1, 10))}]},
    {USERS[0]["user_id"]: [{"file_id": 1, "pages": list(range(1, 6))}]},
    {USERS[1]["user_id"]: [{"file_id": 2, "pages": list(range(1, 13))}]},
    {USERS[1]["user_id"]: [{"file_id": 2, "pages": list(range(1, 6))}]},
    {USERS[0]["user_id"]: [{"file_id": 2, "pages": list(range(1, 13))}]},
    {USERS[0]["user_id"]: [{"file_id": 4, "pages": list(range(1, 61))}]},
]
FILES = [
    {
        "file_id": 1,
        "pages_number": 9,
    },
    {
        "file_id": 2,
        "pages_number": 12,
    },
    {
        "file_id": 3,
        "pages_number": 12,
    },
    {
        "file_id": 4,
        "pages_number": 60,
    },
    {
        "file_id": 5,
        "pages_number": 60,
    },
    {
        "file_id": 6,
        "pages_number": 55,
    },
]

EXPECTED_TASKS = [
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": True,
        "job_id": 1,
        "pages": [6, 7, 8, 9],
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 2,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(1, 13)),
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(1, 10)),
        "user_id": USERS[1]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 2,
        "is_validation": True,
        "job_id": 1,
        "pages": [6, 7, 8, 9, 10, 11, 12],
        "user_id": USERS[1]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 3,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(1, 13)),
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 5,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(1, 51)),
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 5,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(51, 61)),
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(1, 10)),
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 6,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(1, 51)),
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 6,
        "is_validation": True,
        "job_id": 1,
        "pages": list(range(51, 56)),
        "user_id": USERS[0]["user_id"],
        "status": TASKS_STATUS,
    },
]


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["annotated_files_pages", "files", "annotators", "expected_tasks"],
    [
        (
            ANNOTATED_FILES_PAGES[1],
            [copy(FILES[0])],
            [copy(USERS[0])],
            [EXPECTED_TASKS[0]],
        ),
        (
            ANNOTATED_FILES_PAGES[3],
            [copy(FILES[1])],
            [copy(USERS[1])],
            [EXPECTED_TASKS[3]],
        ),
        (
            {**ANNOTATED_FILES_PAGES[0], **ANNOTATED_FILES_PAGES[2]},
            [copy(file) for file in FILES[:2]],
            [copy(annotator) for annotator in USERS[:2]],
            EXPECTED_TASKS[1:3],
        ),
    ],
)
def test_distribute_partial_annotated_left(
    annotated_files_pages, files, annotators, expected_tasks
):
    """Tests that even if annotator has no pages_number left he will get for
    validation pages in files that he didn't annotate.
    """
    assert (
        distribute_validation_partial_files(
            annotated_files_pages,
            files,
            annotators,
            JOB_ID,
            TASKS_STATUS,
        )
        == expected_tasks
    )


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["annotated_files_pages", "files", "annotators", "expected_tasks"],
    [
        (
            ANNOTATED_FILES_PAGES[0],
            [copy(file) for file in FILES[:2]],
            [copy(USERS[0])],
            [EXPECTED_TASKS[1]],
        ),
        (
            ANNOTATED_FILES_PAGES[2],
            [copy(file) for file in FILES[:2]],
            [copy(USERS[1])],
            [EXPECTED_TASKS[2]],
        ),
        (
            ANNOTATED_FILES_PAGES[0],
            [copy(FILES[0])],
            [copy(USERS[0])],
            [],
        ),
    ],
)
def test_validate_not_annotated(
    annotated_files_pages, files, annotators, expected_tasks
):
    assert (
        distribute_validation_partial_files(
            annotated_files_pages,
            files,
            annotators,
            JOB_ID,
            TASKS_STATUS,
        )
        == expected_tasks
    )


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["annotated_files_pages", "files", "annotators", "expected_tasks"],
    [
        (
            ANNOTATED_FILES_PAGES[4],
            [copy(file) for file in FILES[1:3]],
            [copy(USERS[2])],
            [EXPECTED_TASKS[4]],
        ),
        (
            ANNOTATED_FILES_PAGES[5],
            [copy(file) for file in FILES[3:5]],
            [copy(USERS[4])],
            EXPECTED_TASKS[5:7],
        ),
    ],
)
def test_cross_distribution_equal_files(
    annotated_files_pages, files, annotators, expected_tasks
):
    assert (
        distribute_whole_files(
            annotated_files_pages,
            files,
            annotators,
            JOB_ID,
            tasks_status=TASKS_STATUS,
            is_validation=True,
        )
        == expected_tasks
    )


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["annotated_files_pages", "files", "annotators", "expected_tasks"],
    [
        (
            ANNOTATED_FILES_PAGES[5],
            [copy(file) for file in FILES[:3]],
            [copy(USERS[4])],
            [EXPECTED_TASKS[7], EXPECTED_TASKS[1], EXPECTED_TASKS[4]],
        ),
        (
            ANNOTATED_FILES_PAGES[5],
            [copy(FILES[5])],
            [copy(USERS[4])],
            EXPECTED_TASKS[8:10],
        ),
    ],
)
def test_cross_distribution_small_files(
    annotated_files_pages, files, annotators, expected_tasks
):
    assert (
        distribute_whole_files(
            annotated_files_pages,
            files,
            annotators,
            JOB_ID,
            tasks_status=TASKS_STATUS,
            is_validation=True,
        )
        == expected_tasks
    )


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["annotated_files_pages", "files", "annotators", "expected_tasks"],
    [
        (
            ANNOTATED_FILES_PAGES[1],
            [copy(FILES[0])],
            [copy(USERS[2])],
            [EXPECTED_TASKS[0]],
        ),
        (
            ANNOTATED_FILES_PAGES[3],
            [copy(FILES[1])],
            [copy(USERS[3])],
            [EXPECTED_TASKS[3]],
        ),
    ],
)
def test_cross_partial_files(
    annotated_files_pages, files, annotators, expected_tasks
):
    assert (
        distribute_validation_partial_files(
            annotated_files_pages,
            files,
            annotators,
            JOB_ID,
            TASKS_STATUS,
        )
        == expected_tasks
    )
