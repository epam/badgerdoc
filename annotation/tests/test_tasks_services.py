import uuid
from datetime import datetime
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from tenant_dependency import TenantData

from annotation.models import (
    AgreementMetrics,
    AnnotatedDoc,
    ManualAnnotationTask,
)
from annotation.schemas.tasks import (
    AgreementScoreServiceResponse,
    ExportTaskStatsInput,
    ResponseScore,
    TaskStatusEnumSchema,
)
from annotation.tasks import services


@pytest.fixture
def mock_task_revisions():
    yield AnnotatedDoc(
        pages={"1": ["data1"], "2": ["data2"]},
        failed_validation_pages=[1, 2],
        validated=[1, 2],
    )


@pytest.fixture
def mock_metric():
    yield AgreementMetrics(
        task_from=datetime(2024, 1, 1),
        task_to=datetime(2024, 2, 1),
        agreement_metric=True,
    )


@pytest.fixture
def mock_task():
    yield ManualAnnotationTask(
        id=1,
        user_id=2,
        job_id=10,
        file_id=3,
        pages={1, 2, 3},
        is_validation=False,
        status=None,
    )


@pytest.fixture
def mock_stats(
    mock_task: ManualAnnotationTask, mock_metric: ManualAnnotationTask
):
    stat1 = AnnotatedDoc()
    stat1.task = mock_task
    stat1.task_id = 1
    stat1.created = datetime(2024, 1, 1, 12, 0, 0)
    stat1.updated = datetime(2024, 1, 2, 12, 0, 0)

    stat2 = AnnotatedDoc()
    stat2.task = mock_task
    stat2.task_id = 2
    stat2.created = datetime(2024, 1, 3, 12, 0, 0)
    stat2.updated = datetime(2024, 1, 4, 12, 0, 0)

    stat3 = AnnotatedDoc()
    stat3.task = mock_task
    stat3.task_id = 3
    stat3.created = datetime(2024, 1, 5, 12, 0, 0)
    stat3.updated = datetime(2024, 1, 6, 12, 0, 0)
    stat3.task.status = TaskStatusEnumSchema.finished
    yield [stat1, stat2, stat3]


@pytest.fixture
def mock_db(mock_stats: List[AnnotatedDoc]):
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.filter.return_value.all.return_value = (
        mock_stats
    )
    mock_db.query.return_value = mock_query
    yield mock_db


@pytest.fixture
def mock_tenant_data():
    yield TenantData(user_id=1, roles=[], token="mock_token")


@pytest.fixture
def response_scores():
    yield [
        ResponseScore(task_id=2, agreement_score=0.9),
        ResponseScore(task_id=3, agreement_score=0.7),
        ResponseScore(task_id=2, agreement_score=0.9),
    ]


@pytest.fixture
def mock_parse_obj_as():
    with patch("pydantic.parse_obj_as") as mock:
        yield mock


@pytest.fixture
def mock_get_unique_scores():
    with patch(
        "annotation.tasks.services.get_unique_scores", return_value=None
    ) as mock:
        yield mock


@pytest.fixture
def mock_task_metric():
    with patch("annotation.tasks.services.TaskMetric") as mock:
        yield mock


@pytest.fixture
def mock_agreement_score_comparing_result():
    with patch(
        "annotation.tasks.services.AgreementScoreComparingResult"
    ) as mock:
        yield mock


@pytest.fixture
def mock_agreement_score_response():
    mock_response = [
        AgreementScoreServiceResponse(
            job_id=1,
            task_id=1,
            agreement_score=[
                ResponseScore(task_id=2, agreement_score=0.95),
                ResponseScore(task_id=3, agreement_score=0.8),
            ],
            annotator_id=uuid.uuid4(),
        ),
        AgreementScoreServiceResponse(
            job_id=2,
            task_id=1,
            agreement_score=[
                ResponseScore(task_id=1, agreement_score=0.95),
                ResponseScore(task_id=3, agreement_score=0.85),
            ],
            annotator_id=uuid.uuid4(),
        ),
    ]
    yield mock_response


@pytest.fixture
def create_task():
    def _create_task(status: TaskStatusEnumSchema):
        return ManualAnnotationTask(status=status, id=1)

    yield _create_task


@pytest.fixture
def setup_data():
    task_data = {
        "objects": [
            {"id": 1, "name": "Object A", "value": "Some Value", "links": [2]},
            {"id": 2, "name": "Object B", "value": "Another Value"},
        ]
    }
    all_tasks = {
        1: [
            ({"name": "Object A", "value": "Some Value"}, "1"),
            ({"name": "Object C", "value": "Different Value"}, "3"),
        ],
        2: [({"name": "Object B", "value": "Another Value"}, "2")],
    }
    yield task_data, all_tasks


@pytest.fixture
def mock_session():
    with patch("annotation.tasks.services.Session", spec=True) as mock_session:
        yield mock_session()


@pytest.fixture
def mock_validation_revisions():
    with patch(
        "annotation.tasks.services.get_file_path_and_bucket",
        return_value=("s3/path", "bucket"),
    ) as mock_get_file_path_and_bucket, patch(
        "annotation.tasks.services.get_annotation_tasks", return_value={}
    ) as mock_get_annotation_tasks, patch(
        "annotation.tasks.services.construct_annotated_pages",
        return_value=([], set()),
    ) as mock_construct_annotated_pages, patch(
        "annotation.tasks.services.construct_annotated_doc", return_value=None
    ) as mock_construct_annotated_doc, patch(
        "annotation.tasks.services.update_task_status", return_value=None
    ) as mock_update_task_status, patch(
        "annotation.tasks.services.Logger.exception", return_value=None
    ) as mock_logger_exception:
        yield {
            "mock_get_file_path_and_bucket": mock_get_file_path_and_bucket,
            "mock_get_annotation_tasks": mock_get_annotation_tasks,
            "mock_construct_annotated_pages": mock_construct_annotated_pages,
            "mock_construct_annotated_doc": mock_construct_annotated_doc,
            "mock_update_task_status": mock_update_task_status,
            "mock_logger_exception": mock_logger_exception,
        }


def test_get_from_cache():
    objs_ids = {1, 2, 3}
    cache_used = {1: "name1", 3: "name3"}
    objs_names_from_cache, not_cached_usernames = services.get_from_cache(
        objs_ids, cache_used
    )
    expected_objs_names_from_cache = {1: "name1", 3: "name3"}
    expected_not_cached_usernames = {2}
    assert objs_names_from_cache == expected_objs_names_from_cache
    assert not_cached_usernames == expected_not_cached_usernames


def test_get_user_names_by_user_ids():
    user_ids = {1, 2, 3}
    tenant = "test_tenant"
    token = "test_token"
    cached_user_names = {1: "user1", 3: "user3"}
    not_cached_user_ids = {2}
    user_names_from_requests = {2: "user2"}
    with patch(
        "annotation.tasks.services.get_from_cache",
        return_value=(
            cached_user_names,
            not_cached_user_ids,
        ),
    ) as mock_get_from_cache, patch(
        "annotation.tasks.services.get_user_names_by_request",
        return_value=user_names_from_requests,
    ) as mock_get_user_names_by_request, patch(
        "annotation.tasks.services.lru_user_id_to_user_name_cache"
    ) as mock_cache:
        result = services.get_user_names_by_user_ids(user_ids, tenant, token)

        mock_get_from_cache.assert_called_once_with(
            objs_ids=user_ids, cache_used=mock_cache
        )
        mock_get_user_names_by_request.assert_called_once_with(
            user_ids=list(not_cached_user_ids), tenant=tenant, token=token
        )
        mock_cache.update.assert_called_once_with(user_names_from_requests)
        expected_result = {**cached_user_names, **user_names_from_requests}
        assert result == expected_result


def test_get_file_names_by_file_ids():
    file_ids = {1, 2, 3}
    tenant = "test_tenant"
    token = "test_token"
    cached_file_names = {1: "file1", 3: "file3"}
    not_cached_file_ids = {2}
    file_names_from_requests = {2: "file2"}
    with patch(
        "annotation.tasks.services.get_from_cache",
        return_value=(
            cached_file_names,
            not_cached_file_ids,
        ),
    ) as mock_get_from_cache, patch(
        "annotation.tasks.services.get_file_names_by_request",
        return_value=file_names_from_requests,
    ) as mock_get_file_names_by_request, patch(
        "annotation.tasks.services.lru_file_id_to_file_name_cache"
    ) as mock_cache:
        result = services.get_file_names_by_file_ids(file_ids, tenant, token)
        mock_get_from_cache.assert_called_once_with(
            objs_ids=file_ids, cache_used=mock_cache
        )
        mock_get_file_names_by_request.assert_called_once_with(
            file_ids=list(not_cached_file_ids), tenant=tenant, token=token
        )
        mock_cache.update.assert_called_once_with(file_names_from_requests)
        expected_result = {**cached_file_names, **file_names_from_requests}
        assert result == expected_result


@pytest.mark.parametrize(
    "schema",
    (
        ExportTaskStatsInput(
            user_ids=[uuid.uuid4()],
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 6),
        ),
        ExportTaskStatsInput(
            user_ids=[uuid.uuid4(), uuid.uuid4()],
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 6),
        ),
        ExportTaskStatsInput(
            user_ids=[uuid.uuid4()],
            date_from=datetime(2024, 1, 1),
            date_to=None,
        ),
    ),
)
def test_create_export_csv(schema: ExportTaskStatsInput, mock_db: Mock):
    mock_user_name = {2: "user2"}
    mock_file_name = {3: "file3"}
    with patch(
        "annotation.tasks.services.get_user_names_by_user_ids",
        return_value=mock_user_name,
    ) as mock_get_user_names, patch(
        "annotation.tasks.services.get_file_names_by_file_ids",
        return_value=mock_file_name,
    ) as mock_get_file_names, patch(
        "annotation.tasks.services.io.BytesIO"
    ), patch(
        "annotation.tasks.services.io.TextIOWrapper",
    ):
        services.create_export_csv(mock_db, schema, "tenant", "token")
        mock_get_user_names.assert_called_once_with({"2"}, "tenant", "token")
        mock_get_file_names.assert_called_once_with({3}, "tenant", "token")


def test_create_export_csv_no_annotation_stats(mock_db: Mock):
    schema = ExportTaskStatsInput(
        user_ids=[uuid.uuid4()],
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 6),
    )
    filter_mock = (
        mock_db.query.return_value.filter.return_value.filter.return_value
    )
    filter_mock.all.return_value = []
    with patch(
        "annotation.tasks.services.get_user_names_by_user_ids", return_value={}
    ), patch(
        "annotation.tasks.services.get_file_names_by_file_ids", return_value={}
    ), patch(
        "annotation.tasks.services.io.BytesIO"
    ), patch(
        "annotation.tasks.services.io.TextIOWrapper"
    ):
        with pytest.raises(HTTPException) as exc_info:
            services.create_export_csv(mock_db, schema, "tenant", "token")
        assert exc_info.value.status_code == 406
        assert exc_info.value.detail == "Export data not found."
