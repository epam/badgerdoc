from collections import defaultdict
from copy import copy
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from annotation.distribution import (
    add_unassigned_file,
    calculate_users_load,
    distribute_annotation_partial_files,
    distribute_tasks,
    distribute_whole_files,
    find_annotated_pages,
    find_files_for_task,
    find_unassigned_files,
    find_unassigned_pages,
)
from annotation.distribution.main import (
    DistributionUser,
    choose_validators_users,
    create_partial_validation_tasks,
    create_tasks,
    distribute,
    distribute_tasks_extensively,
    find_equal_files,
    find_small_files,
    find_users_share_loads,
    get_page_number_combinations,
    prepare_response,
    prepare_users,
    redistribute,
)
from annotation.microservice_communication.assets_communication import (
    prepare_files_for_distribution,
)
from annotation.microservice_communication.jobs_communication import (
    JobUpdateException,
)
from annotation.models import File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.override_app_dependency import TEST_TENANT


@pytest.fixture
def mock_session(
    tasks_for_test_redistribute: Tuple[ManualAnnotationTask, ...]
):
    mock_db = Mock(spec=Session, flush=Mock(), rollback=Mock())
    mock_db.query.return_value.filter.return_value.all.return_value = (
        tasks_for_test_redistribute
    )
    yield mock_db


@pytest.fixture
def users_for_test_distribute():
    yield (
        User(user_id=1, default_load=10, overall_load=10),
        User(user_id=2, default_load=10, overall_load=10),
        User(user_id=3, default_load=2, overall_load=2),
    )


@pytest.fixture
def tasks_for_test_distribute():
    yield (
        {
            "task_id": 0,
            "file_id": 10,
            "pages": [1, 2, 3],
            "user_id": 1,
        },
        {
            "task_id": 1,
            "file_id": 10,
            "pages": [4, 5, 6],
            "user_id": 2,
        },
        {
            "task_id": 2,
            "file_id": 10,
            "pages": [1, 2, 3, 4, 5, 6],
            "user_id": 2,
        },
    )


@pytest.fixture
def tasks_for_test_redistribute():
    yield (
        ManualAnnotationTask(
            id=0,
            status=TaskStatusEnumSchema.finished,
            is_validation=True,
            file_id=0,
            pages=[1, 2, 3, 4],
        ),
        ManualAnnotationTask(
            id=1,
            status=TaskStatusEnumSchema.finished,
            is_validation=False,
            file_id=1,
            pages=list(range(20)),
        ),
    )


@pytest.fixture
def patch_redistribute_dependencies():
    with patch(
        "annotation.distribution.main.get_pages_in_work",
    ) as mock_get_pages, patch(
        "annotation.distribution.main.distribute",
    ) as mock_distribute, patch(
        "annotation.distribution.main.set_task_statuses"
    ) as mock_set_task_statuses:
        yield mock_get_pages, mock_distribute, mock_set_task_statuses


JOB_ID = 1
ANNOTATORS = [
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "default_load": 100,
        "overall_load": 0,
    },
    {
        "user_id": "ba3e0ccf-8661-4ed3-892b-7c291160f631",
        "default_load": 96,
        "overall_load": 0,
    },
    {
        "user_id": "6e2ce9ac-2fe8-4cc7-bdcd-bac90faa9247",
        "default_load": 95,
        "overall_load": 0,
    },
    {
        "user_id": "8c8a333e-d19a-492a-9e78-5df4bec0ec8b",
        "default_load": 92,
        "overall_load": 0,
    },
    {
        "user_id": "ba38c547-f7f2-4ece-b56f-9926e34b159a",
        "default_load": 90,
        "overall_load": 0,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca56",
        "default_load": 100,
        "overall_load": 50,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca57",
        "default_load": 100,
        "overall_load": 100,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca58",
        "default_load": 0,
        "overall_load": 100,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca59",
        "default_load": 0,
        "overall_load": 50,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca60",
        "default_load": 100,
        "overall_load": 100,
    },
]
FILES = [
    {
        "file_id": 1,
        "pages_number": 31,
    },
    {
        "file_id": 2,
        "pages_number": 25,
    },
    {
        "file_id": 3,
        "pages_number": 16,
    },
    {
        "file_id": 4,
        "pages_number": 15,
    },
    {
        "file_id": 5,
        "pages_number": 14,
    },
    {
        "file_id": 6,
        "pages_number": 10,
    },
]
TASKS_STATUS = TaskStatusEnumSchema.pending


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "test_files",
        "test_annotators",
        "extensive_coverage",
        "expected_share_load",
        "expected_pages_number",
    ],
    [
        (
            FILES,
            ANNOTATORS[0:5],
            1,
            [0.21, 0.2, 0.2, 0.19, 0.19],
            [23, 23, 22, 22, 21],
        ),
        (FILES, [ANNOTATORS[0], ANNOTATORS[4]], 1, [0.53, 0.47], [58, 53]),
        (
            FILES,
            [ANNOTATORS[0], ANNOTATORS[2], ANNOTATORS[4]],
            1,
            [0.35, 0.33, 0.32],
            [39, 37, 35],
        ),
        (
            FILES[0:2],
            [ANNOTATORS[0], ANNOTATORS[7]],
            1,
            [1, 0],
            [56, 0],
        ),
        (
            FILES[2:4],
            [ANNOTATORS[0], ANNOTATORS[8]],
            1,
            [1, 0],
            [31, 0],
        ),
        (
            [FILES[0]],
            [ANNOTATORS[6]],
            1,
            [1],
            [31],
        ),
        (
            [FILES[0]],
            [ANNOTATORS[6], ANNOTATORS[9]],
            1,
            [0.5, 0.5],
            [15, 16],
        ),
        (
            FILES,
            [ANNOTATORS[0], ANNOTATORS[5]],
            1,
            [0.75, 0.25],
            [83, 28],
        ),
        (
            FILES,
            [ANNOTATORS[6], ANNOTATORS[5]],
            1,
            [0.58, 0.42],
            [65, 46],
        ),
        (
            FILES,
            [ANNOTATORS[0], ANNOTATORS[6]],
            1,
            [0.75, 0.25],
            [83, 28],
        ),
        (
            FILES,
            ANNOTATORS,
            1,
            [0.14, 0.13, 0.13, 0.13, 0.13, 0.12, 0.11, 0.11, 0, 0],
            [15, 15, 15, 14, 14, 14, 12, 12, 0, 0, 0],
        ),
        (
            # load is not equal but both annotators should process same amount
            # of pages to cover all of them without duplication for one of them
            FILES,
            [ANNOTATORS[6], ANNOTATORS[5]],
            2,
            [0.58, 0.42],
            [111, 111],
        ),
        (
            # all annotators share duplicated amount of docs based on load
            FILES,
            ANNOTATORS,
            2,
            [0.14, 0.13, 0.13, 0.13, 0.13, 0.12, 0.11, 0.11, 0, 0],
            [31, 30, 29, 29, 28, 27, 24, 24, 0, 0],
        ),
        (  # all annotators share duplicated amount of docs based on load
            FILES,
            ANNOTATORS,
            5,
            [0.14, 0.13, 0.13, 0.13, 0.13, 0.12, 0.11, 0.11, 0, 0],
            [77, 74, 74, 71, 70, 69, 60, 60, 0, 0],
        ),
        (  # all annotators receive full unique subset of documents even
            # though they default load is 0
            # todo validate if this logic is correct.
            FILES,
            ANNOTATORS,
            10,
            [0.14, 0.13, 0.13, 0.13, 0.13, 0.12, 0.11, 0.11, 0, 0],
            [111, 111, 111, 111, 111, 111, 111, 111, 111, 111],
        ),
    ],
)
def test_calculate_annotators_load(
    test_files,
    test_annotators,
    extensive_coverage,
    expected_share_load,
    expected_pages_number,
):
    calculate_users_load(
        test_files, test_annotators, extensive_coverage=extensive_coverage
    )
    for index, annotator in enumerate(test_annotators):
        assert round(annotator["share_load"], 2) == expected_share_load[index]
        assert annotator["pages_number"] == expected_pages_number[index]


@pytest.mark.skip
def test_calculate_users_load_break():
    # Setup file and users to test break condition explicitly
    files = [
        {"file_id": 1, "pages_number": 100}
    ]  # Total number of pages to distribute
    test_annotators = [
        {
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "default_load": 50,
            "overall_load": 0,
        },
        {
            "user_id": "ba3e0ccf-8661-4ed3-892b-7c291160f631",
            "default_load": 50,
            "overall_load": 0,
        },
    ]
    # No extensive coverage
    extensive_coverage = 100

    calculate_users_load(files, test_annotators, extensive_coverage)

    # Assert the pages distributed do not exceed the pages available
    total_distributed_pages = sum(
        annotator["pages_number"] for annotator in test_annotators
    )
    assert total_distributed_pages == files[0]["pages_number"]

    for annotator in test_annotators:
        assert annotator["pages_number"] == 50


ANNOTATORS_WHOLE = [
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "pages_number": 25,
    },
    {
        "user_id": "ba3e0ccf-8661-4ed3-892b-7c291160f631",
        "pages_number": 17,
    },
    {
        "user_id": "6e2ce9ac-2fe8-4cc7-bdcd-bac90faa9247",
        "pages_number": 25,
    },
    {
        "user_id": "8c8a333e-d19a-492a-9e78-5df4bec0ec8b",
        "pages_number": 17,
    },
    {
        "user_id": "ba38c547-f7f2-4ece-b56f-9926e34b159a",
        "pages_number": 4,
    },
    {
        "user_id": "93b973c2-50c7-47ad-b75f-dab44a751a43",
        "pages_number": 4,
    },
    {
        "user_id": "93b973c2-50c7-47ad-b75f-dab44a751a44",
        "pages_number": 4,
    },
    {
        "user_id": "93b973c2-50c7-47ad-b75f-dab44a751a45",
        "pages_number": 4,
    },
]
FILES_WHOLE = [
    {
        "file_id": 2,
        "pages_number": 25,
    },
    {
        "file_id": 3,
        "pages_number": 16,
    },
    {
        "file_id": 4,
        "pages_number": 15,
    },
    {
        "file_id": 5,
        "pages_number": 10,
    },
    {
        "file_id": 7,
        "pages_number": 16,
    },
    {
        "file_id": 6,
        "pages_number": 10,
    },
    {
        "file_id": 5,
        "pages_number": 2,
    },
    {
        "file_id": 8,
        "pages_number": 2,
    },
    {
        "file_id": 9,
        "pages_number": 2,
    },
    {
        "file_id": 10,
        "pages_number": 2,
    },
]
EXPECTED_WHOLE_FILES_TASKS = [
    [
        {
            "deadline": None,
            "file_id": 4,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 5,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 3,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            "user_id": "ba3e0ccf-8661-4ed3-892b-7c291160f631",
            "status": TASKS_STATUS,
        },
    ],
    [
        {
            "deadline": None,
            "file_id": 2,
            "is_validation": False,
            "job_id": 1,
            "pages": [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
            ],
            "user_id": "6e2ce9ac-2fe8-4cc7-bdcd-bac90faa9247",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 7,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            "user_id": "8c8a333e-d19a-492a-9e78-5df4bec0ec8b",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 6,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "user_id": "8c8a333e-d19a-492a-9e78-5df4bec0ec8b",
            "status": TASKS_STATUS,
        },
    ],
    [
        {
            "deadline": None,
            "file_id": 5,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2],
            "user_id": "ba38c547-f7f2-4ece-b56f-9926e34b159a",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 8,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2],
            "user_id": "ba38c547-f7f2-4ece-b56f-9926e34b159a",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 9,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2],
            "user_id": "93b973c2-50c7-47ad-b75f-dab44a751a43",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 10,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2],
            "user_id": "93b973c2-50c7-47ad-b75f-dab44a751a43",
            "status": TASKS_STATUS,
        },
    ],
]
ANNOTATORS_FOR_WHOLE_FILES_UN_PGS = [
    {
        "user_id": "d080408e-0077-4c20-b520-bd4b1541ca59",
        "pages_number": 4,
    },
    {
        "user_id": "d080408e-0077-4c20-b520-bd4b1541ca60",
        "pages_number": 4,
    },
]
FILES_WITH_UNASSIGNED_PAGES = [
    {"file_id": 1, "pages_number": 2, "unassigned_pages": [3, 4]},
    {"file_id": 2, "pages_number": 2, "unassigned_pages": [5, 7]},
    {"file_id": 3, "pages_number": 2, "unassigned_pages": [1, 10]},
    {"file_id": 4, "pages_number": 2},
]
EXPECTED_WHOLE_FILES_TASKS_WITH_UN_PGS = [
    {
        "deadline": None,
        "file_id": FILES_WITH_UNASSIGNED_PAGES[0]["file_id"],
        "is_validation": False,
        "job_id": 1,
        "pages": [3, 4],
        "user_id": ANNOTATORS_FOR_WHOLE_FILES_UN_PGS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": FILES_WITH_UNASSIGNED_PAGES[1]["file_id"],
        "is_validation": False,
        "job_id": 1,
        "pages": [5, 7],
        "user_id": ANNOTATORS_FOR_WHOLE_FILES_UN_PGS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": FILES_WITH_UNASSIGNED_PAGES[2]["file_id"],
        "is_validation": False,
        "job_id": 1,
        "pages": [1, 10],
        "user_id": ANNOTATORS_FOR_WHOLE_FILES_UN_PGS[1]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": FILES_WITH_UNASSIGNED_PAGES[3]["file_id"],
        "is_validation": False,
        "job_id": 1,
        "pages": [1, 2],
        "user_id": ANNOTATORS_FOR_WHOLE_FILES_UN_PGS[1]["user_id"],
        "status": TASKS_STATUS,
    },
]


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["annotation_files", "test_annotators", "expected_whole_files_tasks"],
    [
        (
            [FILES_WHOLE[1], FILES_WHOLE[2], FILES_WHOLE[3]],
            [ANNOTATORS_WHOLE[0], ANNOTATORS_WHOLE[1]],
            EXPECTED_WHOLE_FILES_TASKS[0],
        ),
        (
            [FILES_WHOLE[0], FILES_WHOLE[4], FILES_WHOLE[5]],
            [ANNOTATORS_WHOLE[2], ANNOTATORS_WHOLE[3]],
            EXPECTED_WHOLE_FILES_TASKS[1],
        ),
        (
            [FILES_WHOLE[6], FILES_WHOLE[7], FILES_WHOLE[8], FILES_WHOLE[9]],
            [ANNOTATORS_WHOLE[4], ANNOTATORS_WHOLE[5]],
            EXPECTED_WHOLE_FILES_TASKS[2],
        ),
        (
            FILES_WITH_UNASSIGNED_PAGES,
            ANNOTATORS_FOR_WHOLE_FILES_UN_PGS,
            EXPECTED_WHOLE_FILES_TASKS_WITH_UN_PGS,
        ),
    ],
)
def test_distribute_annotation_whole_files(
    annotation_files, test_annotators, expected_whole_files_tasks
):
    annotation_tasks = distribute_whole_files(
        {},
        annotation_files,
        test_annotators,
        JOB_ID,
        tasks_status=TASKS_STATUS,
        is_validation=False,
    )
    annotation_tasks = [
        {key: value for key, value in task.items() if key != "id"}
        for task in annotation_tasks
    ]
    assert annotation_tasks == expected_whole_files_tasks


def test_distribute_whole_files_pages_number():
    assert (
        distribute_whole_files(
            {},
            [],
            [{"user_id": 0, "pages_number": 0}],
            0,
            False,
            TaskStatusEnumSchema.pending,
        )
        == []
    )


def test_distribute_whole_files_user_page_correction():
    file_list = [
        {"file_id": 1, "pages": 5, "pages_number": 5},
    ]
    user_list = [
        {"user_id": 0, "pages_number": 1},
        {"user_id": 1, "pages_number": 1},
        {"user_id": 2, "pages_number": 1},
    ]
    with patch(
        "annotation.distribution.main.find_small_files",
        return_value=(file_list, 5),
    ):
        assert distribute_whole_files(
            {}, [], user_list, 0, False, TaskStatusEnumSchema.pending
        ) == [
            {
                "deadline": None,
                "file_id": 1,
                "is_validation": False,
                "job_id": 0,
                "pages": [1, 2, 3, 4, 5],
                "status": TaskStatusEnumSchema.pending,
                "user_id": 0,
            },
        ]


def test_distribute_whole_files_break():
    file_list = [
        {"file_id": 1, "pages": 5, "pages_number": 5},
    ]
    user_list = [
        {"user_id": 0, "pages_number": 10},
    ]
    with patch(
        "annotation.distribution.main.find_small_files",
        return_value=(file_list, 15),
    ), patch("annotation.distribution.main.create_tasks"), patch(
        "annotation.distribution.main.find_equal_files",
    ):
        assert (
            distribute_whole_files(
                {}, [], user_list, 0, False, TaskStatusEnumSchema.pending
            )
            == []
        )


ANNOTATOR_PARTIAL = [
    {
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "pages_number": 25,
    },
    {
        "user_id": "ba3e0ccf-8661-4ed3-892b-7c291160f631",
        "pages_number": 20,
    },
    {
        "user_id": "8c8a333e-d19a-492a-9e78-5df4bec0ec8b",
        "pages_number": 15,
    },
    {
        "user_id": "ba38c547-f7f2-4ece-b56f-9926e34b159a",
        "pages_number": 10,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca50",
        "pages_number": 20,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca51",
        "pages_number": 15,
    },
    {
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca52",
        "pages_number": 10,
    },
]
FILES_PARTIAL = [
    {
        "file_id": 1,
        "pages_number": 31,
    },
    {
        "file_id": 5,
        "pages_number": 14,
    },
    {
        "file_id": 11,
        "pages_number": 31,
    },
    {
        "file_id": 12,
        "pages_number": 14,
    },
]
EXPECTED_PARTIAL_FILES_TASKS = [
    [
        {
            "deadline": None,
            "file_id": 1,
            "is_validation": False,
            "job_id": 1,
            "pages": [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
            ],
            "user_id": "ba3e0ccf-8661-4ed3-892b-7c291160f631",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 1,
            "is_validation": False,
            "job_id": 1,
            "pages": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
            "user_id": "8c8a333e-d19a-492a-9e78-5df4bec0ec8b",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 5,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3, 4],
            "user_id": "8c8a333e-d19a-492a-9e78-5df4bec0ec8b",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 5,
            "is_validation": False,
            "job_id": 1,
            "pages": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            "user_id": "ba38c547-f7f2-4ece-b56f-9926e34b159a",
            "status": TASKS_STATUS,
        },
    ],
    [
        {
            "deadline": None,
            "file_id": 11,
            "is_validation": False,
            "job_id": 1,
            "pages": [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
            ],
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 11,
            "is_validation": False,
            "job_id": 1,
            "pages": [26, 27, 28, 29, 30, 31],
            "user_id": "c080408e-0077-4c20-b520-bd4b1541ca50",
            "status": TASKS_STATUS,
        },
        {
            "deadline": None,
            "file_id": 12,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            "user_id": "c080408e-0077-4c20-b520-bd4b1541ca50",
            "status": TASKS_STATUS,
        },
    ],
]
ANNOTATORS_FOR_PARTIAL_FILES_UN_PGS = [
    {
        "user_id": "d080408e-0077-4c20-b520-bd4b1541ca59",
        "pages_number": 15,
    },
    {
        "user_id": "d080408e-0077-4c20-b520-bd4b1541ca60",
        "pages_number": 10,
    },
]
FILES_WITH_UNASSIGNED_PAGES = [
    {
        "file_id": 1,
        "pages_number": 13,
        "unassigned_pages": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25],
    },
    {
        "file_id": 2,
        "pages_number": 12,
        "unassigned_pages": [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
    },
]
EXPECTED_WHOLE_FILES_TASKS_WITH_UN_PGS = [
    {
        "deadline": None,
        "file_id": FILES_WITH_UNASSIGNED_PAGES[0]["file_id"],
        "is_validation": False,
        "job_id": 1,
        "pages": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25],
        "user_id": ANNOTATORS_FOR_PARTIAL_FILES_UN_PGS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": FILES_WITH_UNASSIGNED_PAGES[1]["file_id"],
        "is_validation": False,
        "job_id": 1,
        "pages": [1, 4],
        "user_id": ANNOTATORS_FOR_PARTIAL_FILES_UN_PGS[0]["user_id"],
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": FILES_WITH_UNASSIGNED_PAGES[1]["file_id"],
        "is_validation": False,
        "job_id": 1,
        "pages": [7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
        "user_id": ANNOTATORS_FOR_PARTIAL_FILES_UN_PGS[1]["user_id"],
        "status": TASKS_STATUS,
    },
]


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["annotation_files", "test_annotators", "expected_partial_files_tasks"],
    [
        (
            [FILES_PARTIAL[0], FILES_PARTIAL[1]],
            [ANNOTATOR_PARTIAL[1], ANNOTATOR_PARTIAL[2], ANNOTATOR_PARTIAL[3]],
            EXPECTED_PARTIAL_FILES_TASKS[0],
        ),
        (
            [FILES_PARTIAL[2], FILES_PARTIAL[3]],
            [ANNOTATOR_PARTIAL[0], ANNOTATOR_PARTIAL[4]],
            EXPECTED_PARTIAL_FILES_TASKS[1],
        ),
        (
            FILES_WITH_UNASSIGNED_PAGES,
            ANNOTATORS_FOR_PARTIAL_FILES_UN_PGS,
            EXPECTED_WHOLE_FILES_TASKS_WITH_UN_PGS,
        ),
    ],
)
def test_distribute_annotation_partial_files(
    annotation_files, test_annotators, expected_partial_files_tasks
):
    annotation_tasks = distribute_annotation_partial_files(
        annotation_files, test_annotators, JOB_ID, TASKS_STATUS
    )
    annotation_tasks = [
        {key: value for key, value in task.items() if key != "id"}
        for task in annotation_tasks
    ]
    assert annotation_tasks == expected_partial_files_tasks


def test_distribute_annotation_partial_files_edge_case():
    expected_output = [
        {
            "deadline": None,
            "file_id": 1,
            "is_validation": False,
            "job_id": 1,
            "pages": [1, 2, 3],
            "status": TaskStatusEnumSchema.pending,
            "user_id": 1,
        }
    ]
    with patch("annotation.distribution.main.SPLIT_MULTIPAGE_DOC", True):
        assert (
            distribute_annotation_partial_files(
                [
                    {
                        "unassigned_pages": [1, 2, 3],
                        "pages_number": 3,
                        "file_id": 1,
                    }
                ],
                [{"user_id": 1, "pages_number": 10}],
                1,
                TaskStatusEnumSchema.pending,
            )
            == expected_output
        )


ANNOTATION_TASKS = [
    {
        "deadline": None,
        "file_id": i,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(i + 1)),
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca5" + str(i),
    }
    for i in range(1, 6)
]

ANNOTATED_FILES_PAGES = {
    task["user_id"]: [{"file_id": task["file_id"], "pages": task["pages"]}]
    for task in ANNOTATION_TASKS
}


@pytest.mark.unittest
def test_find_annotated_pages():
    assert find_annotated_pages(ANNOTATION_TASKS) == ANNOTATED_FILES_PAGES


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["task_pages", "expected_files"],
    [
        ([31, 14], [FILES_PARTIAL[0], FILES_PARTIAL[1]]),
        ([31, 31], [FILES_PARTIAL[0], FILES_PARTIAL[2]]),
        ([31, 14, 14], [FILES_PARTIAL[0], FILES_PARTIAL[1], FILES_PARTIAL[3]]),
    ],
)
def test_find_files_for_task(task_pages, expected_files):
    all_files = FILES_PARTIAL
    assert find_files_for_task(all_files, task_pages) == expected_files


FILE_LIMIT_50 = [
    {
        "file_id": 1,
        "pages_number": 160,
    },
    {
        "file_id": 2,
        "pages_number": 50,
    },
    {
        "file_id": 3,
        "pages_number": 50,
    },
]

EXPECTED_TASKS_LIMIT_50 = [
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(1, 51)),
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(51, 101)),
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(101, 151)),
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(151, 161)),
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(101, 121)),
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 1,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(121, 161)),
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca56",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 3,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(1, 51)),
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca56",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 2,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(1, 51)),
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca56",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 3,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(1, 36)),
        "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
        "status": TASKS_STATUS,
    },
    {
        "deadline": None,
        "file_id": 3,
        "is_validation": False,
        "job_id": 1,
        "pages": list(range(36, 51)),
        "user_id": "c080408e-0077-4c20-b520-bd4b1541ca56",
        "status": TASKS_STATUS,
    },
]
EXPECTED_TASKS_NOLIMIT_50 = [
    [
        {
            "file_id": 3,
            "pages": list(range(1, 51)),
            "job_id": 1,
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "is_validation": False,
            "status": TaskStatusEnumSchema.pending,
            "deadline": None,
        }
    ],
    [
        {
            "file_id": 1,
            "pages": list(range(1, 161)),
            "job_id": 1,
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "is_validation": False,
            "status": TaskStatusEnumSchema.pending,
            "deadline": None,
        },
        {
            "file_id": 2,
            "pages": list(range(1, 51)),
            "job_id": 1,
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "is_validation": False,
            "status": TaskStatusEnumSchema.pending,
            "deadline": None,
        },
        {
            "file_id": 3,
            "pages": list(range(1, 51)),
            "job_id": 1,
            "user_id": "c080408e-0077-4c20-b520-bd4b1541ca56",
            "is_validation": False,
            "status": TaskStatusEnumSchema.pending,
            "deadline": None,
        },
    ],
    [
        {
            "file_id": 1,
            "pages": list(range(1, 161)),
            "job_id": 1,
            "user_id": "405ef0e2-b53e-4c18-bf08-c0871615d99d",
            "is_validation": False,
            "status": TaskStatusEnumSchema.pending,
            "deadline": None,
        }
    ],
]


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["files", "annotators", "expected_tasks"],
    [
        (
            [copy(FILE_LIMIT_50[0])],
            [copy(ANNOTATORS[0])],
            EXPECTED_TASKS_NOLIMIT_50[2],
        ),
        (
            [copy(FILE_LIMIT_50[2])],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[5])],
            EXPECTED_TASKS_NOLIMIT_50[0],
        ),
        (
            [copy(test_file) for test_file in FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[5])],
            EXPECTED_TASKS_NOLIMIT_50[1],
        ),
    ],
)
def test_distribute_annotation_limit_50_pages(
    files, annotators, expected_tasks
):
    assert (
        distribute_tasks(
            {},
            files,
            annotators,
            JOB_ID,
            tasks_status=TASKS_STATUS,
            is_validation=False,
        )
        == expected_tasks
    )


@pytest.mark.parametrize(
    ("files", "annotators", "extensive_coverage", "split_multipage_doc_setup"),
    (
        (
            [copy(test_file) for test_file in FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            2,
            "",
        ),
        (
            [copy(test_file) for test_file in FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            3,
            "1",
        ),
        (
            [copy(file) for file in FILES_PARTIAL],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            3,
            "",
        ),
        (
            [copy(file) for file in FILES_PARTIAL[1:] + FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            2,
            "",
        ),
        (
            [copy(file) for file in FILES_PARTIAL[1:] + FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            3,
            "",
        ),
        # function should work distribute with extensive_coverage==1
        (
            [copy(file) for file in FILES_PARTIAL[1:] + FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            1,
            "",
        ),
        (
            [copy(file) for file in FILES_PARTIAL],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            1,
            "",
        ),
    ),
)
def test_distribution_with_extensive_coverage(
    files: List[Dict[str, int]],
    annotators: List[DistributionUser],
    extensive_coverage: int,
    split_multipage_doc_setup: str,
):
    with patch(
        "annotation.distribution.main.SPLIT_MULTIPAGE_DOC",
        split_multipage_doc_setup,
    ):
        tasks = distribute_tasks_extensively(
            files=files,
            users=annotators,
            validators_ids=[],
            job_id=JOB_ID,
            tasks_status=TASKS_STATUS,
            is_validation=False,
            extensive_coverage=extensive_coverage,
        )

    # check all pages were assigned
    all_tasks_pages = sum(len(x["pages"]) for x in tasks)
    all_files_pages = sum(x["pages_number"] for x in files)
    assert all_tasks_pages / extensive_coverage == all_files_pages

    users_seen_pages = defaultdict(lambda: defaultdict(list))
    for task in tasks:
        users_seen_pages[task["user_id"]]["file_id"].extend(task["pages"])

    # check user got assigment without duplicates
    for user in users_seen_pages:
        for file in user:
            assert len(set(users_seen_pages[user][file])) == len(
                users_seen_pages[user][file]
            )


@pytest.mark.unittest
def test_find_unassigned_pages():
    assigned_pages = [1, 3, 5]
    pages_amount = 5
    expected_result = [2, 4]
    actual_result = find_unassigned_pages(assigned_pages, pages_amount)
    assert actual_result == expected_result


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "files_to_distribute",
        "file_id",
        "pages_number",
        "unassigned_pages",
        "expected_result",
    ],
    [
        ([], 1, 10, None, [{"file_id": 1, "pages_number": 10}]),
        (
            [{"file_id": 1, "pages_number": 10}],
            2,
            3,
            [5, 7, 10],
            [
                {"file_id": 1, "pages_number": 10},
                {
                    "file_id": 2,
                    "pages_number": 3,
                    "unassigned_pages": [5, 7, 10],
                },
            ],
        ),
    ],
)
def test_add_unassigned_file(
    files_to_distribute,
    file_id,
    pages_number,
    unassigned_pages,
    expected_result,
):
    add_unassigned_file(
        files_to_distribute, file_id, pages_number, unassigned_pages
    )
    assert files_to_distribute == expected_result


@pytest.mark.unittest
def test_prepare_files_for_distribution():
    files_to_distribute = [
        {"file_id": 1, "pages_number": 2},
        {
            "file_id": 2,
            "pages_number": 3,
            "unassigned_pages": [5, 7, 10],
        },
        {"file_id": 1, "pages_number": 10},
    ]
    expected_result = [
        {"file_id": 1, "pages_number": 10},
        {
            "file_id": 2,
            "pages_number": 3,
            "unassigned_pages": [5, 7, 10],
        },
        {"file_id": 1, "pages_number": 2},
    ]
    actual_result = prepare_files_for_distribution(files_to_distribute)
    assert actual_result == expected_result


PG_FILES = [
    File(
        file_id=1,
        tenant=TEST_TENANT,
        job_id=1,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was fully distributed
    File(
        file_id=2,
        tenant=TEST_TENANT,
        job_id=1,
        pages_number=5,
        distributed_annotating_pages=[],
        annotated_pages=[],
        distributed_validating_pages=[],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was not distributed at all
    File(
        file_id=3,
        tenant=TEST_TENANT,
        job_id=1,
        pages_number=5,
        distributed_annotating_pages=[1, 4],
        annotated_pages=[],
        distributed_validating_pages=[1, 4],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was partially distributed
    File(
        file_id=3,
        tenant=TEST_TENANT,
        job_id=1,
        pages_number=5,
        distributed_annotating_pages=[1, 4],
        annotated_pages=[],
        distributed_validating_pages=[2, 3],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was partially distributed
]


@pytest.mark.unittest
def test_find_unassigned_files():
    expected_result = (
        [
            {
                "file_id": PG_FILES[1].file_id,
                "pages_number": PG_FILES[1].pages_number,
            },
            {
                "file_id": PG_FILES[2].file_id,
                "pages_number": 3,
                "unassigned_pages": [2, 3, 5],
            },
            {
                "file_id": PG_FILES[3].file_id,
                "pages_number": 3,
                "unassigned_pages": [2, 3, 5],
            },
        ],
        [
            {
                "file_id": PG_FILES[1].file_id,
                "pages_number": PG_FILES[1].pages_number,
            },
            {
                "file_id": PG_FILES[2].file_id,
                "pages_number": 3,
                "unassigned_pages": [2, 3, 5],
            },
            {
                "file_id": PG_FILES[3].file_id,
                "pages_number": 3,
                "unassigned_pages": [1, 4, 5],
            },
        ],
    )
    actual_result = find_unassigned_files(PG_FILES)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    ("file_pages", "user_pages", "expected"),
    (
        ([10, 20, 30, 40], 30, [10, 20]),
        ([5, 10, 15, 20], 35, [5, 10, 20]),
        ([10, 20, 30, 40], 100, [10, 20, 30, 40]),
        ([10, 20, 30, 41], 100, []),
        ([], 30, []),
        ([1] * 3000, 1500, [1] * 1500),
    ),
)
def test_get_page_number_combinations(
    file_pages: List[int],
    user_pages: int,
    expected: List[int],
) -> None:
    assert get_page_number_combinations(file_pages, user_pages) == expected


@pytest.mark.parametrize(
    (
        "split_multipage_doc_setup",
        "validation_type",
        "annotation_tasks_ids",
        "expected_output_ids",
    ),
    (
        (
            "",
            ValidationSchema.cross,
            (0, 1),
            (),
        ),
        (
            "1",
            ValidationSchema.hierarchical,
            (1,),
            (2,),
        ),
    ),
)
def test_choose_validators_users(
    split_multipage_doc_setup: str,
    validation_type: ValidationSchema,
    annotation_tasks_ids: Tuple[int, ...],
    expected_output_ids: Tuple[int, ...],
):
    annotators = [{"user_id": 0}, {"user_id": 1}]
    validators = [{"user_id": 2}]

    with patch(
        "annotation.distribution.main.SPLIT_MULTIPAGE_DOC",
        split_multipage_doc_setup,
    ):
        output = choose_validators_users(
            validation_type,
            annotators,
            validators,
            annotation_tasks=[
                {"user_id": user_id} for user_id in annotation_tasks_ids
            ],
        )
        assert tuple(x["user_id"] for x in output) == expected_output_ids


@pytest.mark.parametrize(
    ("users_id", "example_db", "expected_output"),
    (
        (
            [UUID("12345678-1234-5678-1234-567812345678")],
            (UUID("12345678-1234-5678-1234-567812345678"),),
            [User(user_id=UUID("12345678-1234-5678-1234-567812345678"))],
        ),
        (
            [
                UUID("12345678-1234-5678-1234-567812345678"),
                UUID("00d37dc4-b7da-45e5-bcb5-c9b82965351c"),
            ],
            (UUID("12345678-1234-5678-1234-567812345678"),),
            [
                User(user_id=UUID("12345678-1234-5678-1234-567812345678")),
                User(user_id=UUID("00d37dc4-b7da-45e5-bcb5-c9b82965351c")),
            ],
        ),
    ),
)
def test_prepare_users(
    users_id: List[UUID],
    example_db: Tuple[UUID, ...],
    expected_output: List[User],
):
    db = Mock()

    with patch(
        "annotation.distribution.main.read_user",
        side_effect=lambda db, user_id: (
            User(user_id=user_id) if user_id in example_db else None
        ),
    ), patch(
        "annotation.distribution.main.create_user",
        side_effect=lambda db, user_id: User(user_id=user_id),
    ):
        output = prepare_users(db, users_id)
        assert output == expected_output


@pytest.mark.parametrize(
    (
        "users",
        "all_job_pages_sum",
        "average_job_pages",
        "users_default_load",
        "users_overall_load",
        "expected_output",
        "expected_users_share_loads",
    ),
    (
        (
            [{"user_id": "0", "overall_load": 10, "default_load": 10}],
            10,
            10.0,
            10,
            10,
            1.0,
            (1.0,),
        ),
        (
            [
                {"user_id": "0", "overall_load": 10, "default_load": 10},
                {"user_id": "1", "overall_load": 40, "default_load": 20},
            ],
            0,
            25.0,
            10,
            0,
            3.0,
            (1.0, 2.0),
        ),
    ),
)
def test_find_users_share_loads(
    users: List[DistributionUser],
    all_job_pages_sum: int,
    average_job_pages: float,
    users_default_load: int,
    users_overall_load: int,
    expected_output: float,
    expected_users_share_loads: Tuple[float, ...],
):
    output = find_users_share_loads(
        users,
        all_job_pages_sum,
        average_job_pages,
        users_default_load,
        users_overall_load,
    )
    assert output == expected_output
    assert tuple(x["share_load"] for x in users) == expected_users_share_loads


@pytest.mark.parametrize(
    ("files_page_numbers", "user_pages", "expected_output_ids"),
    (
        ((1,), 1, (0,)),
        ((10, 20, 30, 40), 90, (1, 2, 3)),
        ((10, 20, 30, 40), 40, (0, 2)),
        ((10, 10, 10, 20), 40, (0, 1, 3)),
        (
            (10, 20, 30),
            110,
            (),
        ),
    ),
)
def test_find_equal_files(
    files_page_numbers: Tuple[int, ...],
    user_pages: int,
    expected_output_ids: Tuple[int, ...],
):
    file_count = len(files_page_numbers)
    files = [
        {"pages_number": x, "file_id": i}
        for x, i in zip(files_page_numbers, range(file_count))
    ]
    assert (
        tuple(x["file_id"] for x in find_equal_files(files, user_pages))
        == expected_output_ids
    )


@pytest.mark.parametrize(
    (
        "file_page_numbers",
        "user_pages",
        "split_multipage_doc_setup",
        "expected_file_ids",
    ),
    (
        ((10,), 10, "", (0,)),
        ((10, 30, 0), 20, "a", (0,)),
        ((), 100, "", ()),
        ((10, 10, 25), 20, "", (0, 1)),
    ),
)
def test_find_small_files(
    file_page_numbers: Tuple[int, ...],
    user_pages: int,
    split_multipage_doc_setup: str,
    expected_file_ids: Tuple[int, ...],
):
    file_count = len(file_page_numbers)
    files = [
        {"file_id": i, "pages_number": x}
        for i, x in zip(range(file_count), file_page_numbers)
    ]
    with patch(
        "annotation.distribution.main.SPLIT_MULTIPAGE_DOC",
        split_multipage_doc_setup,
    ):
        output, user_page_correction = find_small_files(files, user_pages)
        assert user_page_correction == 0
        assert tuple(x["file_id"] for x in output) == expected_file_ids


def test_prepare_response():
    tasks = [{"user_id": 5}]
    expected_output = tasks
    mock_arg = Mock()

    with patch("annotation.distribution.main.distribute", return_value=tasks):
        assert (
            prepare_response(
                mock_arg,
                mock_arg,
                mock_arg,
                mock_arg,
                mock_arg,
                mock_arg,
                mock_arg,
                mock_arg,
            )
            == expected_output
        )


@pytest.mark.parametrize(
    (
        "unassigned_pages",
        "expected_task_pages",
        "expected_pages_number",
    ),
    (
        ((2, 5, 10), ((2, 5, 10),), 27),
        (
            tuple(range(1, 21)),
            (
                tuple(range(1, 11)),
                tuple(range(11, 21)),
            ),
            10,
        ),
    ),
)
def test_create_tasks(
    unassigned_pages: Tuple[int, ...],
    expected_task_pages: Tuple[Tuple[int, ...], ...],
    expected_pages_number: int,
):
    user = {"user_id": 0, "pages_number": 30}
    tasks = []
    with patch(
        "annotation.distribution.main.SPLIT_MULTIPAGE_DOC",
        True,
    ), patch("annotation.distribution.main.MAX_PAGES", 10):
        create_tasks(
            tasks,
            [
                {
                    "file_id": 0,
                    "unassigned_pages": list(unassigned_pages),
                    "pages_number": len(unassigned_pages),
                }
            ],
            user,
            10,
            False,
            TaskStatusEnumSchema.pending,
        )
        assert [task["pages"] for task in tasks] == [
            list(pages) for pages in expected_task_pages
        ]
        assert user["pages_number"] == expected_pages_number


def test_distribute_main_script(
    mock_session: Mock,
    users_for_test_distribute: Mock,
    tasks_for_test_distribute: Mock,
):
    pages_in_work = {"validation": [tasks_for_test_distribute[0]]}
    tasks = []

    with patch("annotation.distribution.main.create_db_tasks"), patch(
        "annotation.distribution.main.distribute_tasks", return_value=tasks
    ), patch(
        "annotation.distribution.main.distribute_tasks_extensively",
        return_value=tasks,
    ), patch(
        "annotation.distribution.main.remove_pages_in_work"
    ):
        assert (
            distribute(
                mock_session,
                [{"file_id": 0, "pages_number": 6}],
                [],
                [users_for_test_distribute[2]],
                1,
                ValidationSchema.hierarchical,
                [tasks_for_test_distribute[1]],
                extensive_coverage=1,
                pages_in_work=pages_in_work,
            )
            == tasks
        )


def test_distribute_job_validators(
    mock_session: Mock,
    users_for_test_distribute: Mock,
    tasks_for_test_distribute: Mock,
):
    pages_in_work = {"annotation": [tasks_for_test_distribute[0]]}
    tasks = [tasks_for_test_distribute[0], tasks_for_test_distribute[1]]

    with patch("annotation.distribution.main.create_db_tasks"), patch(
        "annotation.distribution.main.distribute_tasks", return_value=tasks
    ), patch(
        "annotation.distribution.main.distribute_tasks_extensively",
        return_value=tasks,
    ), patch(
        "annotation.distribution.main.remove_pages_in_work"
    ):
        assert (
            distribute(
                mock_session,
                [{"file_id": 0, "pages_number": 6}],
                [users_for_test_distribute[1]],
                [users_for_test_distribute[2]],
                1,
                ValidationSchema.cross,
                [],
                extensive_coverage=1,
                pages_in_work=pages_in_work,
            )
            == tasks
        )


def test_distribute_extensive_coverage(
    mock_session: Mock,
    users_for_test_distribute: Mock,
    tasks_for_test_distribute: Mock,
):
    tasks = [tasks_for_test_distribute[2]]

    with patch("annotation.distribution.main.create_db_tasks"), patch(
        "annotation.distribution.main.distribute_tasks", return_value=tasks
    ), patch(
        "annotation.distribution.main.distribute_tasks_extensively",
        return_value=tasks,
    ), patch(
        "annotation.distribution.main.remove_pages_in_work"
    ):
        assert (
            distribute(
                mock_session,
                [{"file_id": 0, "pages_number": 6}],
                [users_for_test_distribute[1]],
                [],
                1,
                ValidationSchema.extensive_coverage,
                [tasks_for_test_distribute[1]],
                extensive_coverage=10,
                pages_in_work=None,
            )
            == tasks
        )


@pytest.mark.parametrize(
    (
        "job_files",
        "job_status",
    ),
    (
        (
            [
                File(file_id=0, pages_number=10),
                File(file_id=1, pages_number=20),
            ],
            JobStatusEnumSchema.in_progress,
        ),
        ([], JobStatusEnumSchema.finished),
    ),
)
def test_redistribute(
    tasks_for_test_redistribute: Mock,
    mock_session: Mock,
    patch_redistribute_dependencies: Mock,
    job_files: List[File],
    job_status: JobStatusEnumSchema,
):
    job_id = 0
    callback_url = "url"
    job = Job(
        job_id=job_id,
        files=job_files,
        status=job_status,
        callback_url=callback_url,
    )
    (
        mock_get_pages,
        mock_distribute,
        mock_set_task_statuses,
    ) = patch_redistribute_dependencies

    with patch(
        "annotation.distribution.main.delete_tasks",
    ) as mock_delete_tasks, patch(
        "annotation.distribution.main.update_job_status",
    ):
        redistribute(mock_session, "dummy_token", "x_tenant", job)
        if job.status == "in_progress":
            mock_set_task_statuses.assert_called_once_with(
                job, tasks_for_test_redistribute
            )
        mock_delete_tasks.assert_called_once_with(mock_session, set())


def test_redistribute_error(
    tasks_for_test_redistribute: Mock,
    mock_session: Mock,
    patch_redistribute_dependencies: Mock,
):
    job_id = 0
    callback_url = "url"
    job = Job(
        job_id=job_id,
        files=[],
        status=JobStatusEnumSchema.in_progress,
        callback_url=callback_url,
    )
    (
        mock_get_pages,
        mock_distribute,
        mock_set_task_statuses,
    ) = patch_redistribute_dependencies

    with patch("annotation.distribution.main.delete_tasks",), patch(
        "annotation.distribution.main.update_job_status",
        side_effect=JobUpdateException("Connection timeout"),
    ) as mock_update_job_status, pytest.raises(HTTPException) as exc_info:
        redistribute(mock_session, "dummy_token", "x_tenant", job)
    mock_update_job_status.assert_called_once_with(
        job.callback_url,
        JobStatusEnumSchema.finished,
        "x_tenant",
        "dummy_token",
    )
    assert exc_info.value.status_code == 500
    assert "Connection timeout" in str(exc_info.value.detail)


def test_create_partial_validation_tasks():
    validation_files_pages = {1: list(range(1, 81))}
    validation_tasks = []
    with patch(
        "annotation.distribution.main.filter_validation_files_pages",
        return_value=validation_files_pages,
    ), patch("annotation.distribution.main.SPLIT_MULTIPAGE_DOC", True):
        create_partial_validation_tasks(
            {},
            [{"user_id": "user1"}, {"user_id": "user2"}],
            {},
            1,
            validation_tasks,
            TaskStatusEnumSchema.pending,
            None,
        )

        assert len(validation_tasks) == 2
        assert validation_tasks[0]["file_id"] == 1
        assert len(validation_tasks[0]["pages"]) == 50
