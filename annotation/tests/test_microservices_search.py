import pytest
import responses
from app.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
)
from app.microservice_communication.jobs_communication import JOBS_SEARCH_URL
from app.microservice_communication.search import (
    PAGE_SIZE,
    calculate_amount_of_pagination_pages,
    construct_search_params,
    expand_response,
    get_response,
)
from app.models import ManualAnnotationTask
from app.schemas import (
    ExpandedManualAnnotationTaskSchema,
    TaskStatusEnumSchema,
)
from fastapi import HTTPException
from requests import ConnectionError, RequestException, Timeout

from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, TEST_TOKEN

AMOUNT_OF_ELEMENTS = 150

IDS = [entity_id for entity_id in range(1, AMOUNT_OF_ELEMENTS)]


SEARCH_PARAMS_FIRST_PAGE = {
    "pagination": {"page_num": 1, "page_size": PAGE_SIZE},
    "filters": [
        {
            "field": "id",
            "operator": "in",
            "value": IDS[0:100],
        }
    ],
    "sorting": [{"field": "id", "direction": "asc"}],
}

SEARCH_PARAMS_PARAMS_SECOND_PAGE = {
    "pagination": {"page_num": 2, "page_size": PAGE_SIZE},
    "filters": [
        {
            "field": "id",
            "operator": "in",
            "value": IDS[100:150],
        }
    ],
    "sorting": [{"field": "id", "direction": "asc"}],
}

ASSETS_FILES = [
    {
        "id": i,
        "original_name": f"some_{i}.pdf",
        "bucket": "tenant1",
        "size_in_bytes": 165887,
        "content_type": "image/png",
        "pages": i,
        "last_modified": "2021-09-28T01:27:55",
        "path": f"files/{i}/{i}.pdf",
        "datasets": [],
    }
    for i in range(1, AMOUNT_OF_ELEMENTS + 1)
]

ASSETS_RESPONSE = {
    "pagination": {
        "page_num": 1,
        "page_size": 15,
        "min_pages_left": 1,
        "total": 3,
        "has_more": False,
    },
    "data": ASSETS_FILES,
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
            "name": "extractionJob1",
            "status": "Pending",
            "files": [1, 2],
            "datasets": [2],
            "creation_datetime": "2021-11-23T12:26:41.669562",
            "type": "ExtractionJob",
            "mode": "Automatic",
            "all_files_data": [
                {
                    "id": 3,
                    "path": "files/3/3.pdf",
                    "pages": 6,
                    "bucket": "tenant1",
                    "status": "uploaded",
                    "datasets": ["dataset22"],
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "last_modified": "2021-11-19T12:26:19.086643",
                    "original_name": "33.pdf",
                    "size_in_bytes": 917433,
                }
            ],
            "pipeline_id": "2",
        },
        {
            "id": 2,
            "name": "annotation_job",
            "status": "Draft",
            "files": [1, 2],
            "datasets": [1],
            "creation_datetime": "2021-11-23T12:30:26.583840",
            "type": "AnnotationJob",
            "mode": "Manual",
            "annotators": [1],
            "categories": [1],
            "is_auto_distribution": False,
            "deadline": "2021-11-28T12:29:44.411000",
        },
    ],
}

FILE_NAMES = {i: f"name_{i}" for i in range(1, 3)}
JOB_NAMES = {i: f"name_{i}" for i in range(1, 3)}
TASKS = [
    ManualAnnotationTask(
        id=1,
        file_id=1,
        pages=[1],
        job_id=1,
        user_id="7b626e68-857d-430a-b65b-bba0a40417ee",
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=2,
        file_id=1,
        pages=[1],
        job_id=2,
        user_id="7b626e68-857d-430a-b65b-bba0a40417ee",
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=3,
        file_id=2,
        pages=[1],
        job_id=2,
        user_id="7b626e68-857d-430a-b65b-bba0a40417ea",
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=4,
        file_id=10,
        pages=[1],
        job_id=10,
        user_id="7b626e68-857d-430a-b65b-bba0a40417eb",
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
    ),
]
USER_LOGINS = {
    TASKS[0].user_id: "test1",
    "7b626e68-857d-430a-b65b-bba0a40417ee": "test1",
    "7b626e68-857d-430a-b65b-bba0a40417ea": "test2",
    "7b626e68-857d-430a-b65b-bba0a40417eb": "test3",
}
EXPANDED_TASKS = [
    ExpandedManualAnnotationTaskSchema(
        id=TASKS[0].id,
        pages=[1],
        user={"id": TASKS[0].user_id, "name": "test1"},
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
        file={"id": TASKS[0].file_id, "name": FILE_NAMES[TASKS[0].file_id]},
        job={"id": TASKS[0].job_id, "name": JOB_NAMES[TASKS[0].job_id]},
    ),
    ExpandedManualAnnotationTaskSchema(
        id=TASKS[1].id,
        pages=[1],
        user={
            "id": "7b626e68-857d-430a-b65b-bba0a40417ee",
            "name": "test1",
        },
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
        file={"id": TASKS[1].file_id, "name": FILE_NAMES[TASKS[1].file_id]},
        job={"id": TASKS[1].job_id, "name": JOB_NAMES[TASKS[1].job_id]},
    ),
    ExpandedManualAnnotationTaskSchema(
        id=TASKS[2].id,
        pages=[1],
        user={
            "id": "7b626e68-857d-430a-b65b-bba0a40417ea",
            "name": "test2",
        },
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
        file={"id": TASKS[2].file_id, "name": FILE_NAMES[TASKS[2].file_id]},
        job={"id": TASKS[2].job_id, "name": JOB_NAMES[TASKS[2].job_id]},
    ),
    ExpandedManualAnnotationTaskSchema(
        id=TASKS[3].id,
        pages=[1],
        user={
            "id": "7b626e68-857d-430a-b65b-bba0a40417eb",
            "name": "test3",
        },
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
        file={"id": TASKS[3].file_id, "name": None},
        job={"id": TASKS[3].job_id, "name": None},
    ),
]


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["elem_amount", "expected_amount_of_pages"], [(50, 1), (100, 1), (101, 2)]
)
def test_calculate_amount_of_pagination_pages(
    elem_amount, expected_amount_of_pages
):
    actual_result = calculate_amount_of_pagination_pages(elem_amount)
    assert actual_result == expected_amount_of_pages


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["page", "ids", "expected_result"],
    [
        (0, IDS, SEARCH_PARAMS_FIRST_PAGE),
        (1, IDS, SEARCH_PARAMS_PARAMS_SECOND_PAGE),
    ],
)
def test_construct_dataset_params(page, ids, expected_result):
    actual_result = construct_search_params(page, ids)
    assert actual_result == expected_result


@pytest.mark.unittest
def test_expand_response():
    actual_result = expand_response(TASKS, FILE_NAMES, JOB_NAMES, USER_LOGINS)
    assert actual_result == EXPANDED_TASKS


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["ids", "url", "is_assets", "microservice_response", "expected_response"],
    [
        (
            IDS,
            ASSETS_FILES_URL,
            True,
            ASSETS_RESPONSE,
            ASSETS_FILES,
        ),
        (
            [JOBS_RESPONSE["data"][0]["id"], JOBS_RESPONSE["data"][1]["id"]],
            JOBS_SEARCH_URL,
            False,
            JOBS_RESPONSE,
            JOBS_RESPONSE["data"],
        ),
        (
            IDS,
            JOBS_SEARCH_URL,
            False,
            {
                "pagination": {
                    "page_num": 1,
                    "page_size": 15,
                    "min_pages_left": 1,
                    "total": 0,
                    "has_more": False,
                },
                "data": [],
            },
            [],
        ),
    ],
)
@responses.activate
def test_get_response(
    ids, url, is_assets, microservice_response, expected_response
):
    responses.add(
        responses.POST,
        url,
        headers=TEST_HEADERS,
        json=microservice_response,
        status=200,
    )
    actual_result = get_response(ids, url, TEST_TENANT, TEST_TOKEN)
    assert actual_result[0:150] == expected_response


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["exc"], [(ConnectionError(),), (Timeout(),), (RequestException(),)]
)
@responses.activate
def test_get_response_exc(exc):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        body=exc,
        status=200,
        headers=TEST_HEADERS,
    )

    with pytest.raises(HTTPException):
        get_response(IDS, ASSETS_FILES_URL, TEST_TENANT, TEST_TOKEN)


@pytest.mark.unittest
@responses.activate
def test_get_datasets_info_bad_status_code():
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        status=500,
    )

    with pytest.raises(HTTPException):
        get_response(IDS, ASSETS_FILES_URL, TEST_TENANT, TEST_TOKEN)
