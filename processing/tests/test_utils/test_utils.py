import json
import uuid

import pytest
import responses
from fastapi import HTTPException

from processing.config import settings
from processing.utils import utils


class MockResponse:
    def __init__(self, text, status):
        self._text = text
        self.status = status

    async def text(self):
        return self._text

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self

    async def json(self):
        return json.loads(self._text)


# -------------------- TESTING list_split -------------------------------


@pytest.mark.parametrize(
    ("value", "threshold", "expected"),
    [
        ([1, 2, 3, 4, 5, 6, 7, 8], 5, [[1, 2, 3, 4, 5], [6, 7, 8]]),
        ([1, 2, 3, 4, 5, 6, 7, 8], 9, [[1, 2, 3, 4, 5, 6, 7, 8]]),
        ([1, 2, 3, 4, 5, 6, 7, 8], 2, [[1, 2], [3, 4], [5, 6], [7, 8]]),
    ],
)
def test_iterable_split(value, threshold, expected):
    assert utils.split_iterable(value, threshold) == expected


# ------------TEST get_files_data_from_separate_files-----------------
@pytest.mark.skip
@responses.activate
def test_positive_get_files_data_from_separate_files(jw_token):
    responses.add(
        responses.POST,
        f"{settings.host_assets}/files/search"
        % {
            "pagination": {"page_num": 1, "page_size": 100},
            "filters": [{"field": "id", "operator": "in", "value": [1, 2]}],
        },
        json={
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
                    "original_name": "3.pdf",
                    "bucket": "tenant1",
                    "size_in_bytes": 44900,
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "pages": 10,
                    "last_modified": "2021-11-19T12:26:18.815466",
                    "status": "uploaded",
                    "path": "files/1/1.pdf",
                    "datasets": ["dataset11"],
                },
                {
                    "id": 2,
                    "original_name": "4.pdf",
                    "bucket": "tenant1",
                    "size_in_bytes": 30111,
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "pages": 2,
                    "last_modified": "2021-11-19T12:26:18.959314",
                    "status": "uploaded",
                    "path": "files/2/2.pdf",
                    "datasets": ["dataset11"],
                },
            ],
        },
        status=200,
    )

    expected_result = (
        [
            {
                "bucket": "tenant1",
                "content_type": "application/pdf",
                "datasets": ["dataset11"],
                "extension": ".pdf",
                "id": 1,
                "last_modified": "2021-11-19T12:26:18.815466",
                "original_name": "3.pdf",
                "pages": 10,
                "path": "files/1/1.pdf",
                "size_in_bytes": 44900,
                "status": "uploaded",
            },
            {
                "bucket": "tenant1",
                "content_type": "application/pdf",
                "datasets": ["dataset11"],
                "extension": ".pdf",
                "id": 2,
                "last_modified": "2021-11-19T12:26:18.959314",
                "original_name": "4.pdf",
                "pages": 2,
                "path": "files/2/2.pdf",
                "size_in_bytes": 30111,
                "status": "uploaded",
            },
        ],
        [1, 2],
    )

    assert utils.get_files_data([1, 2], "test_tenant", jw_token) == expected_result


@pytest.mark.skip
@responses.activate
def test_get_files_data_from_separate_files_100_elements(jw_token):
    large_mock_files_data = {
        "pagination": {
            "page_num": 1,
            "page_size": 100,
            "min_pages_left": 1,
            "total": 2,
            "has_more": False,
        },
        "data": [
            {
                "id": i,
                "original_name": f"{i}.pdf",
                "bucket": "tenant1",
                "size_in_bytes": 44900,
                "extension": ".pdf",
                "content_type": "application/pdf",
                "pages": 10,
                "last_modified": "2021-10-22T07:00:31.964897",
                "status": "uploaded",
                "path": "files/1/1.pdf",
                "datasets": ["dataset11"],
            }
            for i in range(1, 101)
        ],
    }

    responses.add(
        responses.POST,
        f"{settings.host_assets}/files/search"
        % {
            "pagination": {"page_num": 1, "page_size": 100},
            "filters": [
                {
                    "field": "id",
                    "operator": "in",
                    "value": list(range(1, 101)),
                }
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
        json=large_mock_files_data,
        status=200,
    )
    assert utils.get_files_data(list(range(1, 101)), "test_tenant", jw_token) == (
        large_mock_files_data["data"],
        list(range(1, 101)),
    )
    assert len(responses.calls) == 1


@pytest.mark.skip
@responses.activate
def test_get_files_data_from_separate_files_101_elements(jw_token):
    responses.add(
        responses.POST,
        f"{settings.host_assets}/files/search"
        % {
            "pagination": {"page_num": 1, "page_size": 100},
            "filters": [
                {
                    "field": "id",
                    "operator": "in",
                    "value": list(range(1, 101)),
                }
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
        json={
            "pagination": {
                "page_num": 1,
                "page_size": 100,
                "min_pages_left": 1,
                "total": 2,
                "has_more": False,
            },
            "data": [
                {
                    "id": i,
                    "original_name": f"{i}.pdf",
                    "bucket": "tenant1",
                    "size_in_bytes": 44900,
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "pages": 10,
                    "last_modified": "2021-10-22T07:00:31.964897",
                    "status": "uploaded",
                    "path": "files/1/1.pdf",
                    "datasets": ["dataset11"],
                }
                for i in range(1, 101)
            ],
        },
        status=200,
    )

    responses.add(
        responses.POST,
        f"{settings.host_assets}/files/search"
        % {
            "pagination": {"page_num": 2, "page_size": 100},
            "filters": [
                {
                    "field": "id",
                    "operator": "in",
                    "value": 101,
                }
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
        json={
            "pagination": {
                "page_num": 2,
                "page_size": 100,
                "min_pages_left": 1,
                "total": 2,
                "has_more": False,
            },
            "data": [
                {
                    "id": i,
                    "original_name": f"{i}.pdf",
                    "bucket": "tenant1",
                    "size_in_bytes": 44900,
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "pages": 10,
                    "last_modified": "2021-10-22T07:00:31.964897",
                    "status": "uploaded",
                    "path": "files/1/1.pdf",
                    "datasets": ["dataset11"],
                }
                for i in range(101, 102)
            ],
        },
        status=200,
    )
    expected_files_data = [
        {
            "id": i,
            "original_name": f"{i}.pdf",
            "bucket": "tenant1",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 10,
            "last_modified": "2021-10-22T07:00:31.964897",
            "status": "uploaded",
            "path": "files/1/1.pdf",
            "datasets": ["dataset11"],
        }
        for i in range(1, 102)
    ]
    assert utils.get_files_data(list(range(1, 102)), "test_tenant", jw_token) == (
        expected_files_data,
        list(range(1, 102)),
    )
    assert len(responses.calls) == 2


@pytest.mark.skip
@responses.activate
def test_get_files_data_from_separate_files_111_elements(jw_token):
    expected_files_data = [
        {
            "id": i,
            "original_name": f"{i}.pdf",
            "bucket": "tenant1",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 10,
            "last_modified": "2021-10-22T07:00:31.964897",
            "status": "uploaded",
            "path": "files/1/1.pdf",
            "datasets": ["dataset11"],
        }
        for i in range(1, 111)
    ]

    responses.add(
        responses.POST,
        f"{settings.host_assets}/files/search"
        % {
            "pagination": {"page_num": 1, "page_size": 100},
            "filters": [
                {
                    "field": "id",
                    "operator": "in",
                    "value": list(range(1, 101)),
                }
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
        json={
            "pagination": {
                "page_num": 1,
                "page_size": 100,
                "min_pages_left": 1,
                "total": 2,
                "has_more": False,
            },
            "data": [
                {
                    "id": i,
                    "original_name": f"{i}.pdf",
                    "bucket": "tenant1",
                    "size_in_bytes": 44900,
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "pages": 10,
                    "last_modified": "2021-10-22T07:00:31.964897",
                    "status": "uploaded",
                    "path": "files/1/1.pdf",
                    "datasets": ["dataset11"],
                }
                for i in range(1, 101)
            ],
        },
        status=200,
    )

    responses.add(
        responses.POST,
        f"{settings.host_assets}/files/search"
        % {
            "pagination": {"page_num": 2, "page_size": 100},
            "filters": [
                {
                    "field": "id",
                    "operator": "in",
                    "value": list(range(101, 111)),
                }
            ],
            "sorting": [{"field": "id", "direction": "asc"}],
        },
        json={
            "pagination": {
                "page_num": 1,
                "page_size": 100,
                "min_pages_left": 1,
                "total": 2,
                "has_more": False,
            },
            "data": [
                {
                    "id": i,
                    "original_name": f"{i}.pdf",
                    "bucket": "tenant1",
                    "size_in_bytes": 44900,
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "pages": 10,
                    "last_modified": "2021-10-22T07:00:31.964897",
                    "status": "uploaded",
                    "path": "files/1/1.pdf",
                    "datasets": ["dataset11"],
                }
                for i in range(101, 111)
            ],
        },
        status=200,
    )
    assert utils.get_files_data(list(range(1, 111)), "test_tenant", jw_token) == (
        expected_files_data,
        list(range(1, 111)),
    )
    assert len(responses.calls) == 2


@pytest.mark.skip
@responses.activate
def test_get_files_data_from_separate_files_501_code(jw_token):
    request_body = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [{"field": "id", "operator": "eq", "value": "some invalid file id"}],
        "sorting": [{"field": "id", "direction": "asc"}],
    }
    responses.add(
        responses.POST,
        f"{settings.host_assets}/files/search" % request_body,
        json={},
        status=501,
    )
    with pytest.raises(HTTPException) as e_info:
        utils.get_files_data(
            [1234], "testest_execute_pipeline_negativet_tenant", jw_token
        )

    assert e_info.value.status_code == 400


# --------------------- TESTING execute_pipeline -------------------------
@pytest.mark.skip
@responses.activate
def test_execute_pipeline_negative(jw_token, files_data_for_pipeline, db_test_session):

    responses.add(
        responses.POST,
        f"{settings.host_pipelines}/pipelines/2/execute",
        json={},
        status=501,
    )
    with pytest.raises(HTTPException) as e_info:
        utils.execute_pipeline(
            pipeline_id=2,
            files_data=files_data_for_pipeline,
            current_tenant="test_tenant",
            jw_token=jw_token,
            args={"languages": ["en"]},
            batch_id=uuid.uuid4().hex,
            session=db_test_session,
        )

    assert e_info.value.status_code == 400


@pytest.mark.asyncio
async def test_execute_pipeline_positive(
    jw_token, files_data_for_pipeline, db_test_session, mocker
):
    data = [{"id": 1}, {"id": 52}]

    resp = MockResponse(json.dumps(data), 200)

    mocker.patch("aiohttp.ClientSession.request", return_value=resp)

    result = await utils.execute_pipeline(
        pipeline_id=2,
        files_data=files_data_for_pipeline,
        current_tenant="test_tenant",
        jw_token=jw_token,
        args={"type": "postprocessing"},
        batch_id=uuid.uuid4().hex,
        session=db_test_session,
    )
    assert result is None
