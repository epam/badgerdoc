from unittest.mock import Mock

import pytest
import responses
from fastapi import HTTPException
from requests import ConnectionError, RequestException, Timeout
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, TEST_TOKEN

from annotation.microservice_communication.assets_communication import (
    ASSETS_FILES_URL, ASSETS_URL, get_dataset_info, get_file_names,
    get_file_path_and_bucket, get_files_info)

FILES = [
    {
        "id": 1,
        "original_name": "name_1.pdf",
        "bucket": "tenant1",
        "size_in_bytes": 20702285,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 618,
        "last_modified": "2021-11-22T04:26:42.792752",
        "status": "uploaded",
        "path": "files/1/1.pdf",
        "datasets": ["string"],
    },
    {
        "id": 2,
        "original_name": "name_2.pdf",
        "bucket": "tenant1",
        "size_in_bytes": 20597,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 1,
        "last_modified": "2021-11-22T04:26:43.187647",
        "status": "uploaded",
        "path": "files/2/2.pdf",
        "datasets": ["string"],
    },
    {
        "id": 3,
        "original_name": "name_3.pdf",
        "bucket": "tenant1",
        "size_in_bytes": 658529,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 20,
        "last_modified": "2021-11-22T04:26:43.279974",
        "status": "uploaded",
        "path": "files/3/3.pdf",
        "datasets": ["string"],
    },
    {
        "id": 4,
        "original_name": "name_4.pdf",
        "bucket": "tenant1",
        "size_in_bytes": 658529,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 22,
        "last_modified": "2021-11-22T04:26:43.279974",
        "status": "uploaded",
        "path": "files/4/4.pdf",
        "datasets": ["string"],
    },
]

FULL_ASSETS_RESPONSES = [
    {
        "pagination": {
            "page_num": 1,
            "page_size": 15,
            "min_pages_left": 1,
            "total": 3,
            "has_more": False,
        },
        "data": [FILES[0]],
    },
    {
        "pagination": {
            "page_num": 1,
            "page_size": 15,
            "min_pages_left": 1,
            "total": 3,
            "has_more": False,
        },
        "data": [],
    },
]

EXPECTED_FILES_FOR_GET_FILES_INFO = sorted(
    [{"file_id": f["id"], "pages_number": f["pages"]} for f in FILES],
    key=lambda x: x["pages_number"],
    reverse=True,
)

FILE_IDS = [f["id"] for f in FILES]
DATASET_ID = 1

ASSETS_COMPLETE_URL = ASSETS_URL + "/{dataset_id}/files"


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["file_ids", "parsed_response", "expected_result"],
    [
        (
            FILE_IDS,
            FILES,
            {
                1: FILES[0]["original_name"],
                2: FILES[1]["original_name"],
                3: FILES[2]["original_name"],
                4: FILES[3]["original_name"],
            },
        ),
        (FILE_IDS, [], {}),
    ],
)
def test_get_file_names(
    monkeypatch, file_ids, parsed_response, expected_result
):
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication."
        "get_response",
        Mock(return_value=parsed_response),
    )

    actual_result = get_file_names(file_ids, TEST_TENANT, TEST_TOKEN)
    assert actual_result == expected_result


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["returned_files", "expected_result"], [(FILES, FILES), ([], [])]
)
@responses.activate
def test_get_datasets_info(returned_files, expected_result):
    responses.add(
        responses.GET,
        ASSETS_COMPLETE_URL.format(dataset_id=DATASET_ID),
        headers=TEST_HEADERS,
        json=returned_files,
        status=200,
    )

    actual_result = get_dataset_info(DATASET_ID, TEST_TENANT, TEST_TOKEN)
    assert actual_result == expected_result


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["exc"], [(ConnectionError(),), (Timeout(),), (RequestException(),)]
)
@responses.activate
def test_get_datasets_info_request_exc(exc):
    responses.add(
        responses.GET,
        ASSETS_COMPLETE_URL.format(dataset_id=DATASET_ID),
        body=exc,
        headers=TEST_HEADERS,
        status=200,
    )

    with pytest.raises(HTTPException):
        get_dataset_info(DATASET_ID, TEST_TENANT, TEST_TOKEN)


@pytest.mark.unittest
@responses.activate
def test_get_datasets_info_bad_status_code():
    responses.add(
        responses.GET,
        ASSETS_COMPLETE_URL.format(dataset_id=DATASET_ID),
        headers=TEST_HEADERS,
        status=500,
    )

    with pytest.raises(HTTPException):
        get_dataset_info(DATASET_ID, TEST_TENANT, TEST_TOKEN)


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "file_ids",
        "dataset_ids",
        "mocked_files",
        "files_by_dataset_id",
        "expected_result",
    ],
    [
        (
            {1, 2},
            {3, 4},
            FILES[0:2],
            FILES[2:],
            EXPECTED_FILES_FOR_GET_FILES_INFO,
        ),
        ({1, 2, 3, 4}, set(), FILES, [], EXPECTED_FILES_FOR_GET_FILES_INFO),
        (set(), {1, 2, 3, 4}, [], FILES, EXPECTED_FILES_FOR_GET_FILES_INFO),
    ],
)
@responses.activate
def test_get_files_info(
    monkeypatch,
    file_ids,
    dataset_ids,
    mocked_files,
    files_by_dataset_id,
    expected_result,
):
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication."
        "get_response",
        Mock(return_value=mocked_files),
    )
    for i, dataset_id in enumerate(dataset_ids):
        responses.add(
            responses.GET,
            ASSETS_COMPLETE_URL.format(dataset_id=dataset_id),
            json=[files_by_dataset_id[i]],
            headers=TEST_HEADERS,
            status=200,
        )
    actual_result = get_files_info(
        file_ids, dataset_ids, TEST_TENANT, TEST_TOKEN
    )
    assert actual_result == expected_result


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["file_id", "mocked_response", "expected_result"],
    [
        (
            FILES[0]["id"],
            FULL_ASSETS_RESPONSES[0],
            (FILES[0]["path"], (FILES[0]["bucket"])),
        ),
        (100, FULL_ASSETS_RESPONSES[1], (None, None)),
    ],
)
@responses.activate
def test_get_file_path_and_bucket(file_id, mocked_response, expected_result):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=mocked_response,
        headers=TEST_HEADERS,
        status=200,
    )
    actual_result = get_file_path_and_bucket(file_id, TEST_TENANT, TEST_TOKEN)
    assert actual_result == expected_result
