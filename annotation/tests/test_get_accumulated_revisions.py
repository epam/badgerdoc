from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.annotations import LATEST
from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.models import AnnotatedDoc, User
from tests.consts import ANNOTATION_PATH
from tests.override_app_dependency import TEST_TOKEN, app
from tests.test_post_annotation import POST_ANNOTATION_PG_DOC

client = TestClient(app)


def construct_accumulated_revs_path(job_id: int, file_id: int, rev: str):
    return ANNOTATION_PATH + f"/{job_id}/{file_id}/{rev}"


def reformat_date(date: str):
    return date.replace(" ", "T").split(".")[0]


TENANT = POST_ANNOTATION_PG_DOC.tenant
NOT_EXISTING_TENANT = "not-exist"
NOT_EXISTING_ID = 20
FILE_ID = 1
JOB_ID = 1

USERS = [
    User(
        user_id="10df6815-a447-4b93-92d6-f15d69d985e7",
    ),
    User(
        user_id="20df6815-a447-4b93-92d6-f15d69d985e7",
    ),
]

DOCS = [
    AnnotatedDoc(
        revision="1",
        user=USERS[0].user_id,
        pipeline=None,
        file_id=FILE_ID,
        job_id=JOB_ID,
        date="2021-10-01 01:01:01.000000",
        pages={
            "1": "11",
            "2": "21",
        },
        validated=[3],
        failed_validation_pages=[4],
        tenant=TENANT,
    ),
    AnnotatedDoc(
        revision="2",
        user=USERS[0].user_id,
        pipeline=None,
        file_id=FILE_ID,
        job_id=JOB_ID,
        date="2021-10-01 01:01:02.000000",
        pages={
            "3": "32",
        },
        validated=[4],
        failed_validation_pages=[1],
        tenant=TENANT,
    ),
    AnnotatedDoc(
        revision="3",
        user=USERS[1].user_id,
        pipeline=None,
        file_id=FILE_ID,
        job_id=JOB_ID,
        date="2021-10-01 01:01:03.000000",
        pages={
            "1": "13",
            "5": "53",
        },
        validated=[5],
        failed_validation_pages=[],
        tenant=TENANT,
    ),
]

PAGES = {
    DOCS[0].pages["1"]: {
        "page_num": 1,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [{"created": "old"}],
    },
    DOCS[0].pages["2"]: {
        "page_num": 2,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [{"created": "old"}],
    },
    DOCS[1].pages["3"]: {
        "page_num": 3,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [{"created": "old"}],
    },
    DOCS[2].pages["1"]: {
        "page_num": 1,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [{"created": "new"}],
    },
    DOCS[2].pages["5"]: {
        "page_num": 5,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [{"created": "old"}],
    },
}
EMPTY_RESPONSE = dict(
    revision=None,
    user=None,
    pipeline=None,
    date=None,
    pages=[],
    validated=[],
    failed_validation_pages=[],
    categories=None,
)
LATEST_WITH_ALL_PAGES = dict(
    revision=DOCS[2].revision,
    user=DOCS[2].user,
    pipeline=DOCS[2].pipeline,
    date=reformat_date(DOCS[2].date),
    pages=[
        PAGES[DOCS[2].pages["1"]],
        PAGES[DOCS[0].pages["2"]],
        PAGES[DOCS[1].pages["3"]],
        # if there is no annotation for
        # validated pages, this dict will
        # be created
        {
            "page_num": DOCS[1].validated[0],
            "size": {"width": 0.0, "height": 0.0},
            "objs": [],
        },
        PAGES[DOCS[2].pages["5"]],
    ],
    validated=[3, 4, 5],
    failed_validation_pages=[1],
    categories=["test_category_1", "test_category_2"],
)


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "job_id",
        "revision",
        "page_numbers",
        "tenant",
        "expected_response",
    ],
    [
        # find latest revision and accumulate
        # info about all pages
        # from previous revisions
        (
            JOB_ID,
            LATEST,
            {1, 2, 3, 4, 5},
            TENANT,
            LATEST_WITH_ALL_PAGES,
        ),
        # find latest revision and accumulate
        # info about [1, 5] pages
        # from previous revisions
        (
            JOB_ID,
            LATEST,
            {1, 5},
            TENANT,
            dict(
                revision=DOCS[2].revision,
                user=DOCS[2].user,
                pipeline=DOCS[2].pipeline,
                date=reformat_date(DOCS[2].date),
                pages=[
                    PAGES[DOCS[2].pages["1"]],
                    PAGES[DOCS[2].pages["5"]],
                ],
                validated=[5],
                failed_validation_pages=[1],
                categories=["test_category_1", "test_category_2"],
            ),
        ),
        # find first revision and accumulate
        # info about all pages
        # from previous revisions
        # (there are no previous revisions)
        (
            JOB_ID,
            "1",
            {1, 2, 3, 4, 5},
            TENANT,
            dict(
                revision=DOCS[0].revision,
                user=DOCS[0].user,
                pipeline=DOCS[0].pipeline,
                date=reformat_date(DOCS[0].date),
                pages=[
                    PAGES[DOCS[0].pages["1"]],
                    PAGES[DOCS[0].pages["2"]],
                    {
                        "page_num": DOCS[0].validated[0],
                        "size": {"width": 0.0, "height": 0.0},
                        "objs": [],
                    },
                ],
                validated=[3],
                failed_validation_pages=[4],
                categories=["test_category_1", "test_category_2"],
            ),
        ),
        # find first revision and accumulate
        # info about [2, 3, 5] pages
        # from previous revisions
        # (there are no previous revisions)
        (
            JOB_ID,
            "1",
            {2, 3, 5},
            TENANT,
            dict(
                revision=DOCS[0].revision,
                user=DOCS[0].user,
                pipeline=DOCS[0].pipeline,
                date=reformat_date(DOCS[0].date),
                pages=[
                    PAGES[DOCS[0].pages["2"]],
                    {
                        "page_num": DOCS[0].validated[0],
                        "size": {"width": 0.0, "height": 0.0},
                        "objs": [],
                    },
                ],
                validated=[3],
                failed_validation_pages=[],
                categories=["test_category_1", "test_category_2"],
            ),
        ),
        # find second revision and accumulate
        # info about all pages
        # from previous revisions
        (
            JOB_ID,
            "2",
            {1, 2, 3, 4, 5},
            TENANT,
            dict(
                revision=DOCS[1].revision,
                user=DOCS[1].user,
                pipeline=DOCS[1].pipeline,
                date=reformat_date(DOCS[1].date),
                pages=[
                    PAGES[DOCS[0].pages["1"]],
                    PAGES[DOCS[0].pages["2"]],
                    PAGES[DOCS[1].pages["3"]],
                    {
                        "page_num": DOCS[1].validated[0],
                        "size": {"width": 0.0, "height": 0.0},
                        "objs": [],
                    },
                ],
                validated=[3, 4],
                failed_validation_pages=[1],
                categories=["test_category_1", "test_category_2"],
            ),
        ),
        # find second revision and accumulate
        # info about [5] page
        # from previous revisions
        (
            JOB_ID,
            "2",
            {5},
            TENANT,
            dict(
                revision=DOCS[1].revision,
                user=DOCS[1].user,
                pipeline=DOCS[1].pipeline,
                date=reformat_date(DOCS[1].date),
                pages=[],
                validated=[],
                failed_validation_pages=[],
                categories=["test_category_1", "test_category_2"],
            ),
        ),
        # if revisions were not found,
        # there will be empty response
        (
            NOT_EXISTING_ID,
            "2",
            {5},
            TENANT,
            EMPTY_RESPONSE,
        ),
        # if revisions were not found,
        # there will be empty response
        (
            JOB_ID,
            "10",
            {5},
            TENANT,
            EMPTY_RESPONSE,
        ),
        # if there are no pages,
        # info about all pages will be accumulated
        (
            JOB_ID,
            "3",
            {},
            TENANT,
            LATEST_WITH_ALL_PAGES,
        ),
        # bad tenant, empty response
        (
            JOB_ID,
            "3",
            {1},
            NOT_EXISTING_TENANT,
            EMPTY_RESPONSE,
        ),
    ],
)
def test_get_annotation_for_latest_revision_status_codes(
    monkeypatch,
    minio_accumulate_revisions,
    db_accumulated_revs,
    job_id,
    revision,
    page_numbers,
    tenant,
    expected_response,
):
    monkeypatch.setattr(
        "app.annotations.main.connect_s3",
        Mock(return_value=minio_accumulate_revisions),
    )
    monkeypatch.setattr(
        "app.annotations.main.get_file_manifest",
        Mock(
            return_value={"categories": ["test_category_1", "test_category_2"]}
        ),
    )
    params = {"page_numbers": page_numbers}

    response = client.get(
        construct_accumulated_revs_path(job_id, FILE_ID, revision),
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
        params=params,
    )
    accumulated_rev = response.json()
    accumulated_rev["pages"].sort(key=lambda x: x["page_num"])

    assert response.status_code == 200
    assert accumulated_rev == expected_response


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "db_errors",
    ],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_get_annotation_for_latest_revision_db_exceptions(
    monkeypatch, db_errors
):
    response = client.get(
        construct_accumulated_revs_path(
            DOCS[0].job_id,
            DOCS[0].file_id,
            DOCS[0].revision,
        ),
        headers={
            HEADER_TENANT: DOCS[0].tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 500
