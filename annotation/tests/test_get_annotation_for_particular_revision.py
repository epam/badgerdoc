from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.models import AnnotatedDoc, User
from tests.consts import ANNOTATION_PATH
from tests.override_app_dependency import TEST_TENANT, TEST_TOKEN, app

client = TestClient(app)

NOT_EXISTING_TENANT = "not-exist"
NOT_EXISTING_ID = 20

PART_REV_ANNOTATOR = User(
    user_id="40df6815-a447-4b93-92d6-f15d69d985e7",
)

PART_REV_DOC = AnnotatedDoc(
    revision="19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    user=PART_REV_ANNOTATOR.user_id,
    pipeline=None,
    file_id=1,
    job_id=1,
    date="2021-10-01 01:14:01.000000",
    pages={
        "1": "adda414648714f01c1c9657646b72ebb4433c8b5",
        "2": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    },
    validated=[1, 3],
    tenant=TEST_TENANT,
    failed_validation_pages=[],
)

PART_REV_PAGES = [
    {
        "page_num": 1,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [
            {
                "id": 0,
                "type": "string",
                "segmentation": {"segment": "string"},
                "bbox": [0.0, 0.0, 0.0, 0.0],
                "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                "category": "0",
                "data": {},
            }
        ],
    },
    {
        "page_num": 2,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [
            {
                "id": 0,
                "type": "string",
                "segmentation": {"segment": "string"},
                "bbox": [0.0, 0.0, 0.0, 0.0],
                "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                "category": "0",
                "data": {},
            }
        ],
    },
    {
        "page_num": 3,
        "size": {"width": 0.0, "height": 0.0},
        "objs": [],
    },  # this page is validated, but does not have annotation
]

PART_REV_RESPONSE = {
    "revision": PART_REV_DOC.revision,
    "pipeline": None,
    "user": PART_REV_DOC.user,
    "date": "2021-10-01T01:14:01",
    "pages": PART_REV_PAGES,
    "validated": PART_REV_DOC.validated,
    "failed_validation_pages": PART_REV_DOC.failed_validation_pages,
    "categories": None,
}


def construct_part_rev_path(job_id: str, file_id: str, revision: str) -> str:
    return ANNOTATION_PATH + f"/{job_id}/{file_id}/changes/{revision}"


@pytest.mark.integration
@pytest.mark.parametrize(
    ["file_id", "tenant", "expected_code", "expected_response"],
    [
        (
            PART_REV_DOC.file_id,
            PART_REV_DOC.tenant,
            200,
            PART_REV_RESPONSE,
        ),  # get annotation of particular revision
        (
            NOT_EXISTING_ID,
            PART_REV_DOC.tenant,
            404,
            {"detail": "Cannot find such revision(s)."},
        ),  # revision with such file id does not exist
        (
            PART_REV_DOC.file_id,
            NOT_EXISTING_TENANT,
            404,
            {"detail": "Cannot find such revision(s)."},
        ),  # given tenant does not match with revision`s
    ],
)
def test_get_annotation_for_particular_revision_status_codes(
    monkeypatch,
    minio_particular_revision,
    db_particular_revision,
    file_id,
    tenant,
    expected_code,
    expected_response,
):
    monkeypatch.setattr(
        "app.annotations.main.connect_s3",
        Mock(return_value=minio_particular_revision),
    )
    monkeypatch.setattr(
        "app.annotations.main.get_file_manifest",
        Mock(return_value={}),
    )
    response = client.get(
        construct_part_rev_path(
            PART_REV_DOC.job_id, file_id, PART_REV_DOC.revision
        ),
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == expected_code
    assert response.json() == expected_response


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_get_annotation_for_particular_revision_db_exceptions(
    monkeypatch, db_errors
):
    response = client.get(
        construct_part_rev_path(
            PART_REV_DOC.job_id,
            PART_REV_DOC.file_id,
            PART_REV_DOC.revision,
        ),
        headers={
            HEADER_TENANT: PART_REV_DOC.tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 500
