from unittest.mock import patch

import aiohttp.client_exceptions
from tests.test_db import create_mock_annotation_extraction_job_in_db, create_mock_annotation_job_in_db, create_mock_extraction_job_in_db

import pytest
from fastapi import HTTPException
from tests.conftest import FakePipeline, patched_create_pre_signed_s3_url

import jobs.utils as utils
from jobs.schemas import Status, JobMode

# --------------TEST get_files_data_from_datasets---------------


@pytest.mark.asyncio
async def test_positive_get_files_data_from_datasets(
    mock_data_dataset11, mock_data_dataset22, jw_token
):
    with patch(
        "jobs.utils.fetch",
        side_effect=[(200, mock_data_dataset11), (200, mock_data_dataset22)],
    ):
        expected_result = (
            [
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 1,
                    "last_modified": "2021-10-22T07:00:31.964897",
                    "original_name": "3.pdf",
                    "pages": 10,
                    "path": "files/1/1.pdf",
                    "size_in_bytes": 44900,
                    "status": "uploaded",
                },
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 2,
                    "last_modified": "2021-10-22T07:00:32.106530",
                    "original_name": "4.pdf",
                    "pages": 2,
                    "path": "files/2/2.pdf",
                    "size_in_bytes": 30111,
                    "status": "uploaded",
                },
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset22"],
                    "extension": ".pdf",
                    "id": 3,
                    "last_modified": "2021-10-22T07:00:32.239522",
                    "original_name": "33.pdf",
                    "pages": 6,
                    "path": "files/3/3.pdf",
                    "size_in_bytes": 917433,
                    "status": "uploaded",
                },
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset22"],
                    "extension": ".pdf",
                    "id": 4,
                    "last_modified": "2021-10-22T07:00:32.398579",
                    "original_name": "44.pdf",
                    "pages": 32,
                    "path": "files/4/4.pdf",
                    "size_in_bytes": 2680002,
                    "status": "uploaded",
                },
            ],
            [1, 2],
        )

        assert (
            await utils.get_files_data_from_datasets(
                [1, 2], "test_tenant", jw_token
            )
            == expected_result
        )


@pytest.mark.asyncio
async def test_get_files_data_from_datasets_with_one_invalid_tag(
    mock_data_dataset11, jw_token
):
    with patch(
        "jobs.utils.fetch",
        side_effect=[
            (200, mock_data_dataset11),
            (404, {"detail": "Dataset dataset121 does not exist!"}),
        ],
    ):
        expected_result = (
            [
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 1,
                    "last_modified": "2021-10-22T07:00:31.964897",
                    "original_name": "3.pdf",
                    "pages": 10,
                    "path": "files/1/1.pdf",
                    "size_in_bytes": 44900,
                    "status": "uploaded",
                },
                {
                    "bucket": "bucket11",
                    "content_type": "application/pdf",
                    "datasets": ["dataset11"],
                    "extension": ".pdf",
                    "id": 2,
                    "last_modified": "2021-10-22T07:00:32.106530",
                    "original_name": "4.pdf",
                    "pages": 2,
                    "path": "files/2/2.pdf",
                    "size_in_bytes": 30111,
                    "status": "uploaded",
                },
            ],
            [1],
        )
        assert (
            await utils.get_files_data_from_datasets(
                [1, 444], "test_tenant", jw_token
            )
            == expected_result
        )


@pytest.mark.asyncio
async def test_get_files_data_from_datasets_with_all_invalid_tags(jw_token):
    with patch("jobs.utils.fetch", side_effect=[(404, ""), (404, [])]):
        assert await utils.get_files_data_from_datasets(
            [121, 444], "test_tenant", jw_token
        ) == (
            [],
            [],
        )


@pytest.mark.asyncio
async def test_get_files_data_from_datasets_501_error(jw_token):
    with patch(
        "jobs.utils.fetch", side_effect=aiohttp.client_exceptions.ClientError()
    ):
        with pytest.raises(HTTPException) as e_info:
            await utils.get_files_data_from_datasets(
                [121], "test_tenant", jw_token
            )

        assert e_info.value.status_code == 422


# ---------------------TEST get_files_data_from_separate_files-----------------


@pytest.mark.asyncio
async def test_positive_get_files_data_from_separate_files(jw_token):
    json_ = {
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
    }
    with patch("jobs.utils.fetch", return_value=(200, json_)):
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

        assert (
            await utils.get_files_data_from_separate_files(
                [1, 2], "test_tenant", jw_token
            )
            == expected_result
        )


@pytest.mark.asyncio
async def test_get_files_data_from_separate_files_100_elements(jw_token):
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

    with patch(
        "jobs.utils.fetch", return_value=(200, large_mock_files_data)
    ) as mock:
        assert await utils.get_files_data_from_separate_files(
            list(range(1, 101)), "test_tenant", jw_token
        ) == (
            large_mock_files_data["data"],
            list(range(1, 101)),
        )
        mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_files_data_from_separate_files_101_elements(jw_token):
    json_1 = {
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
    json_2 = {
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
    }
    with patch(
        "jobs.utils.fetch", side_effect=[(200, json_1), (200, json_2)]
    ) as mock:
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
        assert await utils.get_files_data_from_separate_files(
            list(range(1, 102)), "test_tenant", jw_token
        ) == (
            expected_files_data,
            list(range(1, 102)),
        )
        assert mock.await_count == 2


@pytest.mark.asyncio
async def test_get_files_data_from_separate_files_111_elements(jw_token):
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
    json_1 = {
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
    json_2 = {
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
    }
    with patch(
        "jobs.utils.fetch", side_effect=[(200, json_1), (200, json_2)]
    ) as mock:
        assert await utils.get_files_data_from_separate_files(
            list(range(1, 111)), "test_tenant", jw_token
        ) == (
            expected_files_data,
            list(range(1, 111)),
        )
        assert mock.await_count == 2


@pytest.mark.asyncio
async def test_get_files_data_from_separate_files_501_code(
    request_body_for_invalid_file, jw_token
):
    with patch(
        "jobs.utils.fetch", side_effect=aiohttp.client_exceptions.ClientError()
    ):
        with pytest.raises(HTTPException) as e_info:
            await utils.get_files_data_from_separate_files(
                [1234], "test_tenant", jw_token
            )

    assert e_info.value.status_code == 422


# --------------------TESTING get_pipeline_id_by_its_name-----------------


@pytest.mark.asyncio
async def test_get_pipeline_id_by_its_name_positive(jw_token):
    json_ = {
        "id": 2,
        "name": "pipeline",
        "version": "v1",
        "date": "2021-09-23T13:45:28.888688",
        "meta": {"name": "pipeline", "version": "v1"},
        "steps": [
            {
                "id": "c56614b0-7b9d-4dd4-a42d-d6a6d447f3b0",
                "name": "first_step",
                "model": "https://de0a3a54-03ef-4d45-9c24-346e45dbc549.mock.pstmn.io/kek1",  # noqa
                "steps": [
                    {
                        "id": "bbc56daf-5a69-46f0-a0af-ea998815c362",
                        "name": "sec",
                        "model": "https://de0a3a54-03ef-4d45-9c24-346e45dbc549.mock.pstmn.io/kek3",  # noqa
                        "label": "table",
                        "steps": [
                            {
                                "id": "63ecbed4-93bc-486c-966b-e7fda8c3cddc",
                                "name": "foo",
                                "model": "https://de0a3a54-03ef-4d45-9c24-346e45dbc549.mock.pstmn.io/kek1",  # noqa
                            }
                        ],
                    },
                    {
                        "id": "8986012f-bb6a-490e-b0e4-da3ef8aed2a9",
                        "name": "foo",
                        "model": "https://de0a3a54-03ef-4d45-9c24-346e45dbc549.mock.pstmn.io/kek1",  # noqa
                        "label": "mrt",
                    },
                ],
            },
            {
                "id": "49ff07bc-0c1d-471f-a62b-60a412c5f779",
                "name": "asd",
                "model": "https://de0a3a54-03ef-4d45-9c24-346e45dbc549.mock.pstmn.io/kek2",  # noqa
            },
        ],
    }
    with patch("jobs.utils.fetch", return_value=(200, json_)):
        res = await utils.get_pipeline_instance_by_its_name(
            "pipeline", "test_tenant", jw_token
        )
        assert res["id"] == 2


@pytest.mark.asyncio
async def test_get_pipeline_id_by_its_name_negative(jw_token):
    with patch(
        "jobs.utils.fetch", side_effect=aiohttp.client_exceptions.ClientError()
    ):
        with pytest.raises(HTTPException) as e_info:
            await utils.get_pipeline_instance_by_its_name(
                "invalid_pipeline_name", "test_tenant", jw_token
            )
        assert e_info.value.status_code == 422


# --------------------- TESTING execute_pipeline -------------------------


@pytest.mark.asyncio
async def test_execute_pipeline_negative(jw_token):
    with patch(
        "jobs.utils.fetch", side_effect=aiohttp.client_exceptions.ClientError()
    ):
        with pytest.raises(HTTPException) as e_info:
            await utils.execute_pipeline(
                pipeline_id=2,
                job_id=2,
                files_data=[{"file_data": "file_data"}],
                current_tenant="test_tenant",
                jw_token=jw_token,
            )

        assert e_info.value.status_code == 422


@pytest.mark.asyncio
async def test_execute_pipeline_positive(jw_token):
    with patch("jobs.utils.fetch", return_value=(200, [{"id": 426}])):
        assert (
            await utils.execute_pipeline(
                pipeline_id=2,
                job_id=2,
                files_data=[{"file_data": "file_data"}],
                current_tenant="test_tenant",
                jw_token=jw_token,
            )
            is None
        )
        
 # -------------------- TESTING job_progress -------------------------------       

@pytest.mark.asyncio
async def test_get_extraction_job_progress_success(testing_session, jw_token: str):
    """Test successful retrieval of job progress."""
    
    job = create_mock_extraction_job_in_db(testing_session)
    job.mode = JobMode.Automatic.value 
    job.pipeline_id = "1" 

    with patch("jobs.utils.fetch", return_value=(200, {"total": 0, "finished": 0})), \
         patch("jobs.airflow_utils.wait_for_dag_completion_async", return_value="success"), \
         patch("jobs.airflow_utils.get_dag_status", return_value={"total": 1, "finished": 1}):
        
        progress = await utils.get_job_progress(
            job_id=job.id,
            session=testing_session,
            current_tenant="test_tenant",
            jw_token=jw_token,
        )

    assert progress is not None
    assert "finished" in progress
    assert progress["total"] == 1
    assert progress["finished"] == 1
    assert "mode" in progress
    assert progress["mode"] == str(job.mode)


@pytest.mark.asyncio
async def test_get_extraction_job_progress_fail(testing_session, jw_token: str):
    """Test fail retrieval of job progress."""
    
    job = create_mock_extraction_job_in_db(testing_session)
    job.mode = JobMode.Automatic.value 
    job.pipeline_id = "1" 

    with patch("jobs.utils.fetch", return_value=(200, {"total": 0, "finished": 0})), \
         patch("jobs.airflow_utils.wait_for_dag_completion_async", return_value="failed"), \
         patch("jobs.airflow_utils.get_dag_status", return_value={"total": 1, "finished": 0}):
        
        progress = await utils.get_job_progress(
            job_id=job.id,
            session=testing_session,
            current_tenant="test_tenant",
            jw_token=jw_token,
        )

    assert progress is not None
    assert "finished" in progress
    assert progress["total"] == 1
    assert progress["finished"] == 0
    assert "mode" in progress
    assert progress["mode"] == str(job.mode)
    

@pytest.mark.asyncio
async def test_get_annotation_job_progress_success(testing_session, jw_token: str, mock_AnnotationJobParams):
    
    job = create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    job.mode = JobMode.Manual.value 

    with patch("jobs.utils.fetch", return_value=(200, {"total": 2, "finished": 2})):
        
        progress = await utils.get_job_progress(
            job_id=job.id,
            session=testing_session,
            current_tenant="test_tenant",
            jw_token=jw_token,
        )

    assert progress is not None
    assert "finished" in progress
    assert progress["total"] == 2
    assert progress["finished"] == 2
    assert "mode" in progress
    assert job.status == "Finished"
    assert progress["mode"] == str(job.mode)

@pytest.mark.asyncio
async def test_get_annotation_job_progress_inProgress(testing_session, jw_token: str, mock_AnnotationJobParams):
    
    job = create_mock_annotation_job_in_db(testing_session, mock_AnnotationJobParams)
    job.mode = JobMode.Manual.value 
    

    with patch("jobs.utils.fetch", return_value=(200, {"total": 3, "finished": 2})):
        
        progress = await utils.get_job_progress(
            job_id=job.id,
            session=testing_session,
            current_tenant="test_tenant",
            jw_token=jw_token,
        )

    assert progress is not None
    assert "finished" in progress
    assert progress["total"] == 3
    assert progress["finished"] == 2
    assert "mode" in progress
    assert job.status == "In Progress"
    assert progress["mode"] == str(job.mode)


@pytest.mark.asyncio
async def test_get_extraction_annotation_job_progress_success(testing_session, jw_token: str, mock_Extraction_AnnotationJobParams):
    
    job = create_mock_annotation_extraction_job_in_db(testing_session, mock_Extraction_AnnotationJobParams)
    job.mode = JobMode.Automatic.value

    with patch("jobs.utils.fetch", return_value=(200, {"total": 2, "finished": 2})):
        
        progress = await utils.get_job_progress(
            job_id=job.id,
            session=testing_session,
            current_tenant="test_tenant",
            jw_token=jw_token,
        )

    assert progress is not None
    assert "finished" in progress
    assert progress["total"] == 2
    assert progress["finished"] == 2
    assert "mode" in progress
    assert job.status == "Finished"
    assert progress["mode"] == str(job.mode)



@pytest.mark.asyncio
async def test_get_extraction_annotation_job_progress_inProgress(testing_session, jw_token: str, mock_Extraction_AnnotationJobParams):
    
    job = create_mock_annotation_extraction_job_in_db(testing_session, mock_Extraction_AnnotationJobParams)
    job.mode = "Automatic" 

    with patch("jobs.utils.fetch", return_value=(200, {"total": 3, "finished": 2})):
        
        progress = await utils.get_job_progress(
            job_id=job.id,
            session=testing_session,
            current_tenant="test_tenant",
            jw_token=jw_token,
        )

    assert progress is not None
    assert "finished" in progress
    assert progress["total"] == 3
    assert progress["finished"] == 2
    assert "mode" in progress
    assert job.status == "In Progress"
    assert progress["mode"] == str(job.mode)


# -------------------- TESTING list_split -------------------------------


@pytest.mark.parametrize(
    ("value", "threshold", "expected"),
    [
        ([1, 2, 3, 4, 5, 6, 7, 8], 5, [[1, 2, 3, 4, 5], [6, 7, 8]]),
        ([1, 2, 3, 4, 5, 6, 7, 8], 9, [[1, 2, 3, 4, 5, 6, 7, 8]]),
    ],
)
def test_list_split(value, threshold, expected):
    assert list(utils.split_list(value, threshold)) == expected


# -------------------- TESTING convert_files_data -------------
@pytest.fixture
def mock_files_data_to_convert():
    mock_files_data_to_convert = [
        {
            "bucket": "bucket11",
            "content_type": "application/pdf",
            "datasets": ["dataset33"],
            "id": 5,
            "last_modified": "2021-09-27T10:43:38",
            "original_name": "33.pdf",
            "pages": 6,
            "size_in_bytes": 917433,
            "uuid_name": "minioadmin/223781a0f9c44bc69daf09e1da6a8c02/223781a0f9c44bc69daf09e1da6a8c02",  # noqa
        },
        {
            "bucket": "bucket11",
            "content_type": "application/pdf",
            "datasets": ["dataset33"],
            "id": 6,
            "last_modified": "2021-09-27T10:43:39",
            "original_name": "44.pdf",
            "pages": 32,
            "size_in_bytes": 2680002,
            "uuid_name": "minioadmin/9949bfab887148e58ae1fdb7209bb1b3/9949bfab887148e58ae1fdb7209bb1b3",  # noqa
        },
    ]
    return mock_files_data_to_convert


@pytest.fixture
def files_data_from_FManager():
    data = [
        {
            "id": 1,
            "original_name": "3.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 10,
            "last_modified": "2021-11-15T07:27:25.508259",
            "status": "uploaded",
            "path": "files/1/1.pdf",
            "datasets": ["dataset11"],
        },
        {
            "id": 2,
            "original_name": "4.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 30111,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 2,
            "last_modified": "2021-11-15T07:27:25.659882",
            "status": "uploaded",
            "path": "files/2/2.pdf",
            "datasets": ["dataset11"],
        },
        {
            "id": 3,
            "original_name": "33.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 917433,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 6,
            "last_modified": "2021-11-15T07:27:25.783934",
            "status": "uploaded",
            "path": "files/3/3.pdf",
            "datasets": ["dataset22"],
        },
        {
            "id": 4,
            "original_name": "44.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 2680002,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 32,
            "last_modified": "2021-11-15T07:27:25.936870",
            "status": "uploaded",
            "path": "files/4/4.pdf",
            "datasets": ["dataset22"],
        },
        {
            "id": 5,
            "original_name": "55.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 965981,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 20,
            "last_modified": "2021-11-15T07:27:26.183839",
            "status": "uploaded",
            "path": "files/5/5.pdf",
            "datasets": ["dataset22"],
        },
    ]
    return data


def test_convert_files_data_for_inference_without_output_bucket(
    files_data_from_FManager,
):
    expected_result = [
        {
            "file": "files/1/1.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 1,
            "output_path": "runs/11/1/1",
            "datasets": ["dataset11"],
        },
        {
            "file": "files/1/1.pdf",
            "bucket": "bucket11",
            "pages": [6, 7, 8, 9, 10],
            "file_id": 1,
            "output_path": "runs/11/1/2",
            "datasets": ["dataset11"],
        },
        {
            "file": "files/2/2.pdf",
            "bucket": "bucket11",
            "pages": [1, 2],
            "file_id": 2,
            "output_path": "runs/11/2",
            "datasets": ["dataset11"],
        },
        {
            "file": "files/3/3.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 3,
            "output_path": "runs/11/3/1",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/3/3.pdf",
            "bucket": "bucket11",
            "pages": [6],
            "file_id": 3,
            "output_path": "runs/11/3/2",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 4,
            "output_path": "runs/11/4/1",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [6, 7, 8, 9, 10],
            "file_id": 4,
            "output_path": "runs/11/4/2",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [11, 12, 13, 14, 15],
            "file_id": 4,
            "output_path": "runs/11/4/3",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [16, 17, 18, 19, 20],
            "file_id": 4,
            "output_path": "runs/11/4/4",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [21, 22, 23, 24, 25],
            "file_id": 4,
            "output_path": "runs/11/4/5",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [26, 27, 28, 29, 30],
            "file_id": 4,
            "output_path": "runs/11/4/6",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [31, 32],
            "file_id": 4,
            "output_path": "runs/11/4/7",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 5,
            "output_path": "runs/11/5/1",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [6, 7, 8, 9, 10],
            "file_id": 5,
            "output_path": "runs/11/5/2",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [11, 12, 13, 14, 15],
            "file_id": 5,
            "output_path": "runs/11/5/3",
            "datasets": ["dataset22"],
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [16, 17, 18, 19, 20],
            "file_id": 5,
            "output_path": "runs/11/5/4",
            "datasets": ["dataset22"],
        },
    ]

    assert (
        utils.convert_files_data_for_inference(
            files_data_from_FManager, 11, pagination_threshold=5
        )
        == expected_result
    )


def test_convert_files_data_for_inference_with_completley_another_output_bucket(  # noqa
    files_data_from_FManager,
):
    expected_result = [
        {
            "file": "files/1/1.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 1,
            "output_path": "runs/11/1/1",
            "datasets": ["dataset11"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/1/1.pdf",
            "bucket": "bucket11",
            "pages": [6, 7, 8, 9, 10],
            "file_id": 1,
            "output_path": "runs/11/1/2",
            "datasets": ["dataset11"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/2/2.pdf",
            "bucket": "bucket11",
            "pages": [1, 2],
            "file_id": 2,
            "output_path": "runs/11/2",
            "datasets": ["dataset11"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/3/3.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 3,
            "output_path": "runs/11/3/1",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/3/3.pdf",
            "bucket": "bucket11",
            "pages": [6],
            "file_id": 3,
            "output_path": "runs/11/3/2",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 4,
            "output_path": "runs/11/4/1",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [6, 7, 8, 9, 10],
            "file_id": 4,
            "output_path": "runs/11/4/2",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [11, 12, 13, 14, 15],
            "file_id": 4,
            "output_path": "runs/11/4/3",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [16, 17, 18, 19, 20],
            "file_id": 4,
            "output_path": "runs/11/4/4",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [21, 22, 23, 24, 25],
            "file_id": 4,
            "output_path": "runs/11/4/5",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [26, 27, 28, 29, 30],
            "file_id": 4,
            "output_path": "runs/11/4/6",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/4/4.pdf",
            "bucket": "bucket11",
            "pages": [31, 32],
            "file_id": 4,
            "output_path": "runs/11/4/7",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [1, 2, 3, 4, 5],
            "file_id": 5,
            "output_path": "runs/11/5/1",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [6, 7, 8, 9, 10],
            "file_id": 5,
            "output_path": "runs/11/5/2",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [11, 12, 13, 14, 15],
            "file_id": 5,
            "output_path": "runs/11/5/3",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
        {
            "file": "files/5/5.pdf",
            "bucket": "bucket11",
            "pages": [16, 17, 18, 19, 20],
            "file_id": 5,
            "output_path": "runs/11/5/4",
            "datasets": ["dataset22"],
            "output_bucket": "another_bucket",
        },
    ]
    assert (
        utils.convert_files_data_for_inference(
            files_data_from_FManager,
            11,
            output_bucket="another_bucket",
            pagination_threshold=5,
        )
        == expected_result
    )


def test_delete_duplicates():
    test_input = [
        {
            "id": 1,
            "original_name": "3.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 10,
            "last_modified": "2021-10-22T07:00:31.964897",
            "status": "uploaded",
            "path": "files / 1 / 1.pdf",
            "datasets": ["dataset11"],
        },
        {
            "id": 2,
            "original_name": "4.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 30111,
            "extension": ".pdf",
            "content_type": "application / pdf",
            "pages": 2,
            "last_modified": "2021 - 10 - 22T07: 00: 32.106530",
            "status": "uploaded",
            "path": "files / 2 / 2.pdf",
            "datasets": ["dataset11"],
        },
        {
            "id": 1,
            "original_name": "3.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application / pdf",
            "pages": 10,
            "last_modified": "2021 - 10 - 22T07: 00:31.964897",
            "status": "uploaded",
            "path": "files / 1 / 1.pdf",
            "datasets": ["dataset11"],
        },
        {
            "id": 2,
            "original_name": "4.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 30111,
            "extension": ".pdf",
            "content_type": "application / pdf",
            "pages": 2,
            "last_modified": "2021 - 10 - 22T07: 00:32.106530",
            "status": "uploaded",
            "path": "files / 2 / 2.pdf",
            "datasets": ["dataset11"],
        },
    ]

    expected_result = [
        {
            "bucket": "bucket11",
            "content_type": "application / pdf",
            "datasets": ["dataset11"],
            "extension": ".pdf",
            "id": 1,
            "last_modified": "2021 - 10 - 22T07: 00:31.964897",
            "original_name": "3.pdf",
            "pages": 10,
            "path": "files / 1 / 1.pdf",
            "size_in_bytes": 44900,
            "status": "uploaded",
        },
        {
            "bucket": "bucket11",
            "content_type": "application / pdf",
            "datasets": ["dataset11"],
            "extension": ".pdf",
            "id": 2,
            "last_modified": "2021 - 10 - 22T07: 00:32.106530",
            "original_name": "4.pdf",
            "pages": 2,
            "path": "files / 2 / 2.pdf",
            "size_in_bytes": 30111,
            "status": "uploaded",
        },
    ]
    assert utils.delete_duplicates(test_input) == expected_result


def test_delete_duplicates_same_data_but_different_ids():
    test_input = [
        {
            "id": 1,
            "original_name": "3.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 10,
            "last_modified": "2021-10-22T07:00:31.964897",
            "status": "uploaded",
            "path": "files / 1 / 1.pdf",
            "datasets": ["dataset11"],
        },
        {
            "id": 2,
            "original_name": "3.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 10,
            "last_modified": "2021-10-22T07:00:31.964897",
            "status": "uploaded",
            "path": "files / 1 / 1.pdf",
            "datasets": ["dataset11"],
        },
    ]
    assert utils.delete_duplicates(test_input) == test_input


def test_delete_duplicates_3():
    test_file_data = {
        "id": 1,
        "original_name": "3.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 44900,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 10,
        "last_modified": "2021-10-22T07:00:31.964897",
        "status": "uploaded",
        "path": "files / 1 / 1.pdf",
        "datasets": ["dataset11"],
    }
    test_input = [
        test_file_data,
        test_file_data,
        test_file_data,
        test_file_data,
    ]
    assert utils.delete_duplicates(test_input) == [test_file_data]


def test_delete_duplicates_4():
    test_file_data1 = {
        "id": 1,
        "original_name": "3.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 44900,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 10,
        "last_modified": "2021-10-22T07:00:31.964897",
        "status": "uploaded",
        "path": "files / 1 / 1.pdf",
        "datasets": ["dataset11"],
    }
    test_file_data2 = {
        "id": 2,
        "original_name": "3.pdf",
        "bucket": "bucket11",
        "size_in_bytes": 44900,
        "extension": ".pdf",
        "content_type": "application/pdf",
        "pages": 10,
        "last_modified": "2021-10-22T07:00:31.964897",
        "status": "uploaded",
        "path": "files / 1 / 1.pdf",
        "datasets": ["dataset11"],
    }
    test_input = [
        test_file_data1,
        test_file_data2,
        test_file_data1,
        test_file_data2,
        test_file_data1,
        test_file_data2,
    ]
    assert utils.delete_duplicates(test_input) == [
        test_file_data1,
        test_file_data2,
    ]


@pytest.mark.parametrize("sign_s3_links", [True, False])
@pytest.mark.asyncio
async def test_execute_external_pipeline(sign_s3_links: bool):
    with patch(
        "jobs.utils.airflow_utils.AirflowPipeline", new=FakePipeline
    ), patch("jobs.utils.JOBS_SIGNED_URL_ENABLED", new=sign_s3_links), patch(
        "jobs.utils.create_pre_signed_s3_url",
        new=patched_create_pre_signed_s3_url,
    ):
        await utils.execute_external_pipeline(
            pipeline_id="2",
            pipeline_engine="airflow",
            job_id=2,
            files_data=[
                {
                    "bucket": "test",
                    "file": f"files/1/1.{sign_s3_links}.pdf",
                    "pages": [1, 2, 3],
                    "output_path": "runs/1/1",
                    "datasets": ["dataset11"],
                }
            ],
            previous_jobs_data=[],
            current_tenant="test_tenant",
            datasets=[{"id": 1, "name": "dataset11"}],
            revisions=[],
        )

        assert FakePipeline.calls
        assert FakePipeline.calls[-1].get("files")
        if sign_s3_links:
            assert (
                f"/test/files/1/1.{sign_s3_links}.pdf"
                in FakePipeline.calls[-1]["files"][0].get("signed_url")
            )
        else:
            assert FakePipeline.calls[-1]["files"][0].get("signed_url") is None
