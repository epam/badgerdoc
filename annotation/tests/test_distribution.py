from collections import defaultdict
from copy import copy

import pytest

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
from annotation.distribution.main import distribute_tasks_extensively
from annotation.microservice_communication.assets_communication import (
    prepare_files_for_distribution,
)
from annotation.models import File
from annotation.schemas import FileStatusEnumSchema, TaskStatusEnumSchema
from tests.override_app_dependency import TEST_TENANT

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


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["files", "annotators", "expected_tasks"],
    [
        (
            [copy(FILE_LIMIT_50[0])],
            [copy(ANNOTATORS[0])],
            EXPECTED_TASKS_LIMIT_50[:4],
        ),
        (
            [copy(FILE_LIMIT_50[0])],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[5])],
            EXPECTED_TASKS_LIMIT_50[:2] + EXPECTED_TASKS_LIMIT_50[4:6],
        ),
        (
            [copy(test_file) for test_file in FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[5])],
            EXPECTED_TASKS_LIMIT_50[:4] + EXPECTED_TASKS_LIMIT_50[7:10],
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


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["files", "annotators", "extensive_coverage"],
    [
        (
            [copy(test_file) for test_file in FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            2,
        ),
        (
            [copy(test_file) for test_file in FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            3,
        ),
        (
            [copy(file) for file in FILES_PARTIAL],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            3,
        ),
        (
            [copy(file) for file in FILES_PARTIAL[1:] + FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            2,
        ),
        (
            [copy(file) for file in FILES_PARTIAL[1:] + FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            3,
        ),
        # function should work distribute with extensive_coverage==1
        (
            [copy(file) for file in FILES_PARTIAL[1:] + FILE_LIMIT_50],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            1,
        ),
        (
            [copy(file) for file in FILES_PARTIAL],
            [copy(ANNOTATORS[0]), copy(ANNOTATORS[2]), copy(ANNOTATORS[3])],
            1,
        ),
    ],
)
@pytest.mark.unittest
def test_distribution_with_extensive_coverage(
    files, annotators, extensive_coverage
):
    tasks = distribute_tasks_extensively(
        files=files,
        users=annotators,
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
