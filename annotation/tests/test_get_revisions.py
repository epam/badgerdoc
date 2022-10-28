from unittest.mock import Mock, patch

import boto3
import pytest
from botocore.exceptions import BotoCoreError
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.annotations import S3_START_PATH
from tests.consts import ANNOTATION_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app

JOBS_IDS = (
    1,
    2,
    3,
    4,
    5,
    6,
)
FILES_IDS = (
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
)
USERS_IDS = (
    "e4090c2d-a6e3-4c49-bf44-cab41fcfb477",
    "709011b6-37fd-40d4-b39a-5aa2cbe292ab",
)
PIPELINES = (
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
)
PAGE = {
    "page_number": 1,
    "size": {"width": float(1), "height": float(1)},
    "objs": [
        {
            "id": 1,
            "type": "string",
            "segmentation": {"segment": "string"},
            "bbox": [float(1), float(1), float(1), float(1)],
            "links": [{"category_id": 1, "to": 1, "page_num": 1}],
            "category": "1",
            "data": {},
        }
    ],
}
PAGES_IDS = (
    "977167c24363b8f568466ac0d6bd90483be84fb8",
    "c50746413101877a1984aab8b0014f938cec28a3",
    "5375722263c50a9daae2559fd74e410539247c51",
    "67461f9ed2560858343f847937a90c117c89c46e",
    "c78abd5c49b55b8f6b92ef955596a29d3c9bb834",
    "f5189b077cdcc26753332daaa79937d2416a6a4a",
    "9c92d0ed6a2ba4642725714827b111f202eed3cc",
    "0951fa9039671fc81a817443fb96a1de42ae07df",
    "a9728565c877464ebf746dace730d879f833b6fc",
    "889e2c06b53d7c777da04a0b8478ca126174f7a9",
    "5fb8fbcdaa884493fa5acf4351db3f1629b7c72f",
    "bf2c48551926f2c45b71515c114643e417642149",
)
REVISIONS_IDS = (
    "84f0e265c1a5eddd5b57348d4c79056293740336",
    "93a79659cb6cd74407d6bd611b38f7a94973b7a8",
    "cdb6e03f11490153e043057edd8d6c0ec2da26c4",
    "a6b3a23a9533ab372a60b6de231d1d90760bbd1b",
    "99f77738127b9e37741fc5db492844e28c69918e",
    "4b8cf2f79b5dbbedf6a7b90c87f6c8a1c6b9d28b",
    "06535d71000ce6df1f2574df489be0b9a8efade8",
    "cc0c49b892596477fed97c868daa895d0798ce76",
    "b7ec83174ae47d7df82d3f18d2412496b7e296e4",
    "7a3258fc75fb595c190405d8163b5b8472cb021c",
    "8a3258fc75fb595c190405d8163b5b8472cb021c",
    "9a3258fc75fb595c190405d8163b5b8472cb022c",
    "9a3258fc75fb595c190405d8163b5b8472cb023c",
    "9a3258fc75fb595c190405d8163b5b8472cb024c",
    "9a3258fc75fb595c190405d8163b5b8472cb025c",
    "9a3258fc75fb595c190405d8163b5b8472cb026c",
    "9a3258fc75fb595c190405d8163b5b8472cb027c",
    "9a3258fc75fb595c190405d8163b5b8472cb028c",
)
REVISIONS = (
    {
        "revision": REVISIONS_IDS[0],
        "user": USERS_IDS[0],
        "pipeline": None,
        "date": "2021-10-01 01:01:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[0],
        "pages": {"1": PAGES_IDS[0]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[1],
        "user": USERS_IDS[1],
        "pipeline": None,
        "date": "2021-10-01 01:02:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[0],
        "pages": {"2": PAGES_IDS[1]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[2],
        "user": USERS_IDS[0],
        "pipeline": None,
        "date": "2021-10-01 01:03:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[0],
        "pages": {"1": PAGES_IDS[2], "2": PAGES_IDS[3]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[3],
        "user": USERS_IDS[1],
        "pipeline": None,
        "date": "2021-10-01 01:04:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[0],
        "pages": {"3": PAGES_IDS[4]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[4],
        "user": USERS_IDS[0],
        "pipeline": None,
        "date": "2021-10-01 01:05:01.000000",
        "file_id": FILES_IDS[1],
        "job_id": JOBS_IDS[0],
        "pages": {"1": PAGES_IDS[5], "2": PAGES_IDS[6]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[5],
        "user": USERS_IDS[1],
        "pipeline": None,
        "date": "2021-10-01 01:06:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[0],
        "pages": {"1": PAGES_IDS[7]},
        "validated": [2],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[6],
        "user": USERS_IDS[0],
        "pipeline": None,
        "date": "2021-10-01 01:07:01.000000",
        "file_id": FILES_IDS[1],
        "job_id": JOBS_IDS[0],
        "pages": {},
        "validated": [3],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[7],
        "user": USERS_IDS[1],
        "pipeline": None,
        "date": "2021-10-01 01:08:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[1],
        "pages": {"1": PAGES_IDS[8], "2": PAGES_IDS[9]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[8],
        "user": USERS_IDS[1],
        "pipeline": None,
        "date": "2021-10-01 01:09:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[0],
        "pages": {},
        "validated": [1],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[9],
        "user": USERS_IDS[0],
        "pipeline": None,
        "date": "2021-10-01 01:10:01.000000",
        "file_id": FILES_IDS[1],
        "job_id": JOBS_IDS[1],
        "pages": {"1": PAGES_IDS[10], "2": PAGES_IDS[11]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[12],
        "user": None,
        "pipeline": PIPELINES[2],
        "date": "2021-10-01 01:12:01.000000",
        "file_id": FILES_IDS[2],
        "job_id": JOBS_IDS[2],
        "pages": {"1": PAGES_IDS[0]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[13],
        "user": None,
        "pipeline": PIPELINES[3],
        "date": "2021-10-01 01:13:01.000000",
        "file_id": FILES_IDS[3],
        "job_id": JOBS_IDS[2],
        "pages": {"1": PAGES_IDS[0]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[14],
        "user": None,
        "pipeline": PIPELINES[4],
        "date": "2021-10-01 01:14:01.000000",
        "file_id": FILES_IDS[4],
        "job_id": JOBS_IDS[3],
        "pages": {"1": PAGES_IDS[0]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[15],
        "user": None,
        "pipeline": PIPELINES[5],
        "date": "2021-10-01 01:15:01.000000",
        "file_id": FILES_IDS[5],
        "job_id": JOBS_IDS[4],
        "pages": {"1": PAGES_IDS[0]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[16],
        "user": None,
        "pipeline": PIPELINES[6],
        "date": "2021-10-01 01:16:01.000000",
        "file_id": FILES_IDS[6],
        "job_id": JOBS_IDS[4],
        "pages": {"1": PAGES_IDS[0]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[17],
        "user": None,
        "pipeline": PIPELINES[7],
        "date": "2021-10-01 01:16:01.000000",
        "file_id": FILES_IDS[7],
        "job_id": JOBS_IDS[5],
        "pages": {"1": PAGES_IDS[0]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[10],
        "user": None,
        "pipeline": PIPELINES[0],
        "date": "2021-10-01 01:10:01.000000",
        "file_id": FILES_IDS[1],
        "job_id": JOBS_IDS[1],
        "pages": {"1": PAGES_IDS[10], "2": PAGES_IDS[11]},
        "validated": [],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
    {
        "revision": REVISIONS_IDS[11],
        "user": None,
        "pipeline": PIPELINES[1],
        "date": "2021-10-01 01:09:01.000000",
        "file_id": FILES_IDS[0],
        "job_id": JOBS_IDS[0],
        "pages": {},
        "validated": [1],
        "tenant": TEST_TENANT,
        "failed_validation_pages": [],
    },
)


def build_pages_paths(revisions):
    pages_paths = []
    for revision in revisions:
        for _, page_id in revision["pages"].items():
            pages_paths.append(
                f"{S3_START_PATH}/{revision['job_id']}/{revision['file_id']}/"
                f"{page_id}.json",
            )
    return tuple(pages_paths)


PAGES_PATHS = build_pages_paths(REVISIONS)
client = TestClient(app)


@pytest.mark.integration
@patch.object(Session, "query")
def test_get_latest_revision_by_user_sql_connection_error(
    Session,
    prepare_db_for_get_revisions,
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(
        f"{ANNOTATION_PATH}/{JOBS_IDS[0]}/{FILES_IDS[0]}/latest_by_user",
        headers=TEST_HEADERS,
        params={"page_numbers": [1]},
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@patch.object(boto3, "resource")
def test_get_latest_revision_by_user_s3_connection_error(
    boto3,
    prepare_db_for_get_revisions,
):
    boto3.side_effect = Mock(side_effect=BotoCoreError())
    response = client.get(
        f"{ANNOTATION_PATH}/{JOBS_IDS[0]}/{FILES_IDS[0]}/latest_by_user",
        headers=TEST_HEADERS,
        params={"page_numbers": [1]},
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@patch.object(Session, "query")
def test_get_all_revisions_sql_connection_error(
    Session, prepare_db_for_get_revisions
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(
        f"{ANNOTATION_PATH}/{JOBS_IDS[0]}/{FILES_IDS[0]}",
        headers=TEST_HEADERS,
        params={"page_numbers": [1]},
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@patch.object(boto3, "resource")
def test_get_all_revisions_s3_connection_error(
    boto3, prepare_db_for_get_revisions
):
    boto3.side_effect = Mock(side_effect=BotoCoreError())
    response = client.get(
        f"{ANNOTATION_PATH}/{JOBS_IDS[0]}/{FILES_IDS[0]}",
        headers=TEST_HEADERS,
        params={"page_numbers": [1]},
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "tenant",
        "job_id",
        "file_id",
        "user_id",
        "page_numbers",
        "expected_status_code",
        "expected_response_key",
    ],
    [
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            None,
            [1],
            200,
            "0",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            None,
            [2],
            200,
            "1",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            None,
            [1, 2],
            200,
            "2",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[1],
            None,
            [3],
            200,
            "3",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[0],
            None,
            [1, 2],
            200,
            "4",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[1],
            None,
            [1, 2],
            200,
            "5",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            USERS_IDS[0],
            [1],
            200,
            "6",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            USERS_IDS[0],
            [2],
            200,
            "7",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            USERS_IDS[0],
            [1, 2],
            200,
            "8",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[1],
            USERS_IDS[0],
            [3],
            200,
            "9",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[0],
            USERS_IDS[0],
            [1, 2],
            200,
            "17",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[1],
            USERS_IDS[0],
            [1, 2],
            200,
            "10",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            USERS_IDS[1],
            [1],
            200,
            "11",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            USERS_IDS[1],
            [2],
            200,
            "12",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            USERS_IDS[1],
            [1, 2],
            200,
            "13",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[1],
            USERS_IDS[1],
            [3],
            200,
            "18",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[0],
            USERS_IDS[1],
            [1, 2],
            200,
            "14",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[1],
            USERS_IDS[1],
            [1, 2],
            200,
            "17",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[2],
            FILES_IDS[2],
            None,
            [1],
            200,
            "16",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[2],
            FILES_IDS[2],
            USERS_IDS[0],
            [1],
            200,
            "15",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[3],
            FILES_IDS[2],
            None,
            [1],
            200,
            "15",
        ),
    ],
)
def test_get_latest_revision_by_user(
    monkeypatch,
    prepare_db_for_get_revisions,
    prepare_moto_s3_for_get_revisions,
    expected_latest_revisions,
    tenant,
    job_id,
    file_id,
    user_id,
    page_numbers,
    expected_status_code,
    expected_response_key,
):
    monkeypatch.setattr(
        "app.annotations.main.connect_s3",
        Mock(return_value=prepare_moto_s3_for_get_revisions),
    )
    response = client.get(
        f"{ANNOTATION_PATH}/{job_id}/{file_id}/latest_by_user",
        headers=TEST_HEADERS,
        params={"user_id": user_id, "page_numbers": page_numbers},
    )
    assert response.status_code == expected_status_code
    assert response.json() == expected_latest_revisions[expected_response_key]


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "tenant",
        "job_id",
        "file_id",
        "page_numbers",
        "expected_status_code",
        "expected_response_key",
    ],
    [
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            [1],
            200,
            "0",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            [2],
            200,
            "1",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            [1, 2],
            200,
            "2",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[0],
            [4],
            200,
            "9",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[0],
            FILES_IDS[1],
            [3],
            200,
            "3",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[0],
            [1, 2],
            200,
            "4",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[1],
            [1, 2],
            200,
            "5",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[1],
            FILES_IDS[1],
            [3],
            200,
            "8",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[4],
            FILES_IDS[5],
            [1],
            200,
            "7",
        ),
        (
            TEST_TENANT,
            JOBS_IDS[5],
            FILES_IDS[5],
            [1],
            200,
            "6",
        ),
    ],
)
def test_get_all_revisions(
    monkeypatch,
    prepare_db_for_get_revisions,
    prepare_moto_s3_for_get_revisions,
    expected_all_revisions,
    tenant,
    job_id,
    file_id,
    page_numbers,
    expected_status_code,
    expected_response_key,
):
    monkeypatch.setattr(
        "app.annotations.main.connect_s3",
        Mock(return_value=prepare_moto_s3_for_get_revisions),
    )
    response = client.get(
        f"{ANNOTATION_PATH}/{job_id}/{file_id}",
        headers=TEST_HEADERS,
        params={"page_numbers": page_numbers},
    )
    assert response.status_code == expected_status_code
    assert response.json() == expected_all_revisions[expected_response_key]
