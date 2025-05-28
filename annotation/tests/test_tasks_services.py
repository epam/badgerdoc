import re
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from fastapi import HTTPException
from tenant_dependency import TenantData

from annotation.errors import CheckFieldError, FieldConstraintError
from annotation.filters import TaskFilter
from annotation.jobs.services import ValidationSchema
from annotation.models import (
    AgreementMetrics,
    AnnotatedDoc,
    AnnotationStatistics,
    File,
    ManualAnnotationTask,
)
from annotation.schemas.annotations import PageSchema, ParticularRevisionSchema
from annotation.schemas.tasks import (
    AgreementScoreComparingResult,
    AgreementScoreServiceResponse,
    AnnotationStatisticsEventEnumSchema,
    AnnotationStatisticsInputSchema,
    ExportTaskStatsInput,
    ManualAnnotationTaskInSchema,
    ResponseScore,
    TaskMetric,
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
    stat1 = AnnotationStatistics(
        task=mock_task,
        task_id=1,
        created=datetime.utcnow(),
        updated=datetime.utcnow(),
    )
    stat2 = AnnotationStatistics(
        task=mock_task,
        task_id=2,
        created=datetime.utcnow(),
        updated=datetime.utcnow(),
    )
    stat3 = AnnotationStatistics(
        task=mock_task,
        task_id=3,
        created=datetime.utcnow(),
        updated=datetime.utcnow(),
    )
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
    yield TenantData(
        user_id=str(1),
        roles=[],
        token="mock_token",
        tenants=["local"],
    )


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
def mock_get_file_path_and_bucket():
    with patch(
        "annotation.tasks.services.get_file_path_and_bucket",
        return_value=("s3/path", "bucket"),
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_annotation_tasks():
    with patch(
        "annotation.tasks.services.get_annotation_tasks", return_value={}
    ) as mock:
        yield mock


@pytest.fixture
def mock_construct_annotated_pages():
    yield PageSchema(
        page_num=10,
        size={"width": 10.2, "height": 123.34},
        objs=[
            {
                "id": 2,
                "type": "string",
                "original_annotation_id": "int",
                "segmentation": {"segment": "string"},
                "bbox": [10.2, 123.34, 34.2, 43.4],
                "tokens": None,
                "links": [{"category_id": "1", "to": 2, "page_num": 2}],
                "text": "text in object",
                "category": "3",
                "data": "string",
                "children": [1, 2, 3],
            },
            {
                "id": 3,
                "type": "string",
                "segmentation": {"segment": "string"},
                "bbox": None,
                "tokens": ["token-string1", "token-string2", "token-string3"],
                "links": [{"category_id": "1", "to": 2, "page_num": 3}],
                "text": "text in object",
                "category": "3",
                "data": "string",
                "children": [1, 2, 3],
            },
        ],
    )


@pytest.fixture
def mock_construct_annotated_doc():
    with patch(
        "annotation.tasks.services.construct_annotated_doc", return_value=None
    ) as mock:
        yield mock


@pytest.fixture
def mock_update_task_status():
    with patch(
        "annotation.tasks.services.update_task_status", return_value=None
    ) as mock:
        yield mock


@pytest.fixture
def mock_logger_exception():
    with patch("annotation.tasks.services.Logger.exception") as mock:
        yield mock


@pytest.mark.parametrize(
    ("validation_type", "is_validation"),
    (
        (ValidationSchema.validation_only, True),
        ("other_type", False),
        ("other_type", True),
    ),
)
def test_validate_task_info(
    validation_type: ValidationSchema,
    is_validation: bool,
):
    with patch(
        "annotation.tasks.services.validate_users_info"
    ) as mock_validate_users_info, patch(
        "annotation.tasks.services.validate_files_info"
    ) as mock_validate_files_info:
        task_info = {"is_validation": is_validation}
        services.validate_task_info(None, task_info, validation_type)
        mock_validate_users_info.assert_called_once_with(
            None, task_info, validation_type
        )
        mock_validate_files_info.assert_called_once_with(None, task_info)


def test_validate_task_info_invalid_task_info():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {"is_validation": False}
        validation_type = ValidationSchema.validation_only
        with pytest.raises(FieldConstraintError):
            services.validate_task_info(db_session, task_info, validation_type)


@pytest.mark.parametrize("is_validation", (True, False))
def test_validate_users_info(is_validation: bool):
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {
            "is_validation": is_validation,
            "user_id": 1,
            "job_id": 2,
        }
        db_session.query().filter_by().first().return_value = True
        services.validate_users_info(
            db_session, task_info, ValidationSchema.validation_only
        )
        assert db_session.query.call_count == 2


def test_validate_users_info_cross_validation(mock_session: Mock):
    with patch(
        "annotation.tasks.services.check_cross_annotating_pages"
    ) as mock_func:
        task_info = {
            "is_validation": True,
            "user_id": 1,
            "job_id": 2,
        }
        services.validate_users_info(
            mock_session, task_info, ValidationSchema.cross
        )
        mock_func.assert_called_once_with(mock_session, task_info)


@pytest.mark.parametrize(
    ("is_validation", "validator_or_annotator"),
    ((True, "validator"), (False, "annotator")),
)
def test_validate_users_info_invalid_users_info(
    mock_session: Mock,
    is_validation: bool,
    validator_or_annotator: str,
):
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {
            "is_validation": is_validation,
            "user_id": 1,
            "job_id": 2,
        }
        db_session.query().filter_by().first.return_value = None
        expected_error_message = (
            f"user 1 is not assigned as {validator_or_annotator} for job 2"
        )
        with pytest.raises(FieldConstraintError, match=expected_error_message):
            services.validate_users_info(
                db_session, task_info, ValidationSchema.validation_only
            )


def test_validate_files_info():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {
            "file_id": 1,
            "job_id": 2,
            "pages": [1, 2, 3],
        }
        mock_file = Mock(spec=File)
        mock_file.pages_number = 3
        mock_query = db_session.query.return_value
        mock_query.filter_by.return_value.first.return_value = mock_file
        services.validate_files_info(db_session, task_info)
        assert db_session.query.call_count == 1
        db_session.query.assert_has_calls((call(File),))
        mock_query.filter_by.assert_called_once_with(file_id=1, job_id=2)


def test_validate_files_info_invalid_page_numbers():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {
            "file_id": 1,
            "job_id": 2,
            "pages": [1, 2, 4],
        }
        mock_file = Mock(spec=File, pages_number=3)
        db_session.query().filter_by().first.return_value = mock_file
        expected_error_message_regex = r"pages \(\{4\}\) do not belong to file"
        with pytest.raises(
            FieldConstraintError, match=expected_error_message_regex
        ):
            services.validate_files_info(db_session, task_info)


def test_validate_files_info_missing_file():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {
            "file_id": 1,
            "job_id": 2,
            "pages": [1, 2, 3],
        }
        db_session.query().filter_by().first.return_value = None
        expected_error_message_regex = (
            r"file with id 1 is not assigned for job 2"
        )
        with pytest.raises(
            FieldConstraintError, match=expected_error_message_regex
        ):
            services.validate_files_info(db_session, task_info)


def test_check_cross_annotating_pages():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {"user_id": 1, "file_id": 2, "job_id": 3, "pages": {4, 5}}
        existing_pages = []
        mock_query = db_session.query.return_value
        mock_query.filter.return_value.all.return_value = [(existing_pages,)]
        services.check_cross_annotating_pages(db_session, task_info)
        assert db_session.query.call_count == 1
        db_session.query.assert_has_calls((call(ManualAnnotationTask.pages),))
        mock_query.filter.assert_called_once()


def test_check_cross_annotating_pages_page_already_annotated():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {"user_id": 1, "file_id": 2, "job_id": 3, "pages": {4, 5}}
        existing_pages = [4, 5]
        mock_query = db_session.query.return_value
        mock_query.filter.return_value.all.return_value = [(existing_pages,)]
        with pytest.raises(
            FieldConstraintError, match=".*tasks for this user: {4, 5}.*"
        ):
            services.check_cross_annotating_pages(db_session, task_info)


@pytest.mark.parametrize(
    (
        "failed",
        "annotated",
        "annotation_user",
        "validation_user",
        "expected_error_message_pattern",
    ),
    (
        (
            {1},
            set(),
            False,
            True,
            r"Missing `annotation_user_for_failed_pages` param",
        ),
        (
            set(),
            {2},
            True,
            False,
            r"Missing `validation_user_for_reannotated_pages` param",
        ),
    ),
)
def test_validate_user_actions_missing_users(
    failed: set,
    annotated: set,
    annotation_user: bool,
    validation_user: bool,
    expected_error_message_pattern: str,
):
    with pytest.raises(HTTPException) as excinfo:
        services.validate_user_actions(
            is_validation=True,
            failed=failed,
            annotated=annotated,
            not_processed=set(),
            annotation_user=annotation_user,
            validation_user=validation_user,
        )
    assert re.match(expected_error_message_pattern, excinfo.value.detail)


@pytest.mark.parametrize(
    (
        "failed",
        "annotated",
        "not_processed",
        "expected_error_message_pattern",
    ),
    (
        (
            set(),
            set(),
            set(),
            r"Validator did not mark any pages as failed",
        ),
        (
            {1},
            set(),
            set(),
            r"Validator did not edit any pages",
        ),
        (
            {1},
            {2},
            {3},
            r"Cannot finish validation task. There are not processed pages",
        ),
    ),
)
def test_validate_user_actions_invalid_states(
    failed: set,
    annotated: set,
    not_processed: set,
    expected_error_message_pattern: str,
):
    with pytest.raises(HTTPException) as excinfo:
        services.validate_user_actions(
            is_validation=True,
            failed=failed,
            annotated=annotated,
            not_processed=not_processed,
            annotation_user=True,
            validation_user=True,
        )
    assert re.match(expected_error_message_pattern, excinfo.value.detail)


def test_create_annotation_task(mock_session: Mock):
    with patch("annotation.tasks.services.update_user_overall_load"):
        result = services.create_annotation_task(
            mock_session,
            ManualAnnotationTaskInSchema(
                file_id=1,
                pages={1, 2},
                job_id=2,
                user_id=uuid.uuid4(),
                is_validation=True,
                deadline=None,
            ),
        )
        assert result.file_id == 1
        assert result.pages == {1, 2}
        assert result.job_id == 2
        assert result.is_validation is True
        assert result.deadline is None
        assert mock_session.add.call_count == 1
        mock_session.commit.assert_called_once()


def test_read_annotation_tasks_with_file_and_job_ids(mock_session: Mock):
    mock_query = mock_session.query.return_value
    mock_query.filter_by.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.limit.return_value.offset.return_value.all.return_value = [
        "task1"
    ]
    total_objects, annotation_tasks = services.read_annotation_tasks(
        db=mock_session,
        search_params={"file_ids": [1, 2], "job_ids": [3]},
        pagination_page_size=10,
        pagination_start_page=1,
        tenant="example_tenant",
    )
    assert total_objects == 1
    assert annotation_tasks == ["task1"]
    mock_query.filter_by.assert_called_once()
    mock_query.limit.assert_called_once_with(10)


@pytest.mark.parametrize(
    ("search_id", "search_name", "ids_with_names", "expected_result"),
    (
        (1, "Task 1", {1: "Task 1", 2: "Task 2"}, ([1], {1: "Task 1"})),
        (1, None, {1: "Task 1", 2: "Task 2"}, ([1], {})),
    ),
)
def test_validate_ids_and_names(
    search_id: int,
    search_name: Optional[str],
    ids_with_names: Dict[int, str],
    expected_result: Tuple[List[int], Dict[int, str]],
):
    result = services.validate_ids_and_names(
        search_id=search_id,
        search_name=search_name,
        ids_with_names=ids_with_names,
    )
    assert result == expected_result


@pytest.mark.parametrize(
    ("search_id", "search_name", "ids_with_names"),
    (
        (3, "Task 3", {1: "Task 1", 2: "Task 2"}),
        (1, "Task 1", {}),
        (None, "Task 2", None),
    ),
)
def test_validate_ids_and_names_invalid_name_or_id(
    search_id: Optional[int],
    search_name: str,
    ids_with_names: Optional[Dict[int, str]],
):
    with pytest.raises(HTTPException) as exc_info:
        services.validate_ids_and_names(
            search_id=search_id,
            search_name=search_name,
            ids_with_names=ids_with_names,
        )
    assert exc_info.value.status_code == 404


def test_remove_additional_filters_with_standard_filters():
    filter_args = {
        "filters": [
            {"field": "normal_field", "value": "value1"},
            {"field": "normal_field_2", "value": "value2"},
        ],
        "sorting": [{"field": "normal_field", "order": "asc"}],
    }
    expected_filters = deepcopy(filter_args)
    expected_additional_filters = {}
    result = services.remove_additional_filters(filter_args)
    assert filter_args == expected_filters
    assert result == expected_additional_filters


def test_remove_additional_filters_with_additional_fields():
    filter_args = {
        "filters": [
            {"field": "file_name", "value": ["file1", "file2"]},
            {"field": "job_name", "value": "job1"},
        ],
        "sorting": [],
    }
    expected_filters = {
        "filters": [],
        "sorting": [],
    }
    expected_additional_filters = {
        "file_name": ["file1", "file2"],
        "job_name": ["job1"],
    }
    result = services.remove_additional_filters(filter_args)
    assert filter_args == expected_filters
    assert result == expected_additional_filters


def test_read_annotation_task(mock_session: Mock):
    expected_result = "task1"
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = expected_result
    result = services.read_annotation_task(
        mock_session, task_id=1, tenant="tenant_1"
    )
    assert result == expected_result
    mock_session.query.assert_called_once_with(ManualAnnotationTask)
    mock_query.filter.assert_called_once()
    mock_filter.first.assert_called_once()


def test_filter_tasks_db_no_additional_filters(mock_session: Mock):
    request = TaskFilter()
    tenant = "test_tenant"
    token = "test_token"
    with patch(
        "annotation.tasks.services.map_request_to_filter"
    ) as mock_map_request_to_filter, patch(
        "annotation.tasks.services.remove_additional_filters"
    ) as mock_remove_additional_filters, patch(
        "annotation.microservice_communication."
        "assets_communication.get_files_by_request"
    ) as mock_get_files_by_request, patch(
        "annotation.jobs.services.get_jobs_by_name"
    ) as mock_get_jobs_by_name, patch(
        "annotation.tasks.services.form_query"
    ) as mock_form_query, patch(
        "annotation.tasks.services.paginate"
    ) as mock_paginate:
        mock_query = MagicMock(return_value=[])
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_paginate.return_value = ([], MagicMock())
        mock_map_request_to_filter.return_value = {
            "filters": [],
            "sorting": [],
        }
        mock_remove_additional_filters.return_value = {}
        mock_get_files_by_request.return_value = {}
        mock_get_jobs_by_name.return_value = {}
        mock_form_query.return_value = (MagicMock(), MagicMock())
        mock_paginate.return_value = []
        result = services.filter_tasks_db(mock_session, request, tenant, token)
        assert result == ([], {}, {})


def test_filter_tasks_db_file_and_job_name(mock_session: Mock):
    additional_filters = {"file_name": ["file1"], "job_name": ["job1"]}
    files_by_name = {"file1": 1}
    jobs_by_name = {"job1": 1}
    expected_result = ([MagicMock()], {"file1": 1}, {"job1": 1})
    request = TaskFilter()
    tenant = "test_tenant"
    token = "test_token"
    with patch(
        "annotation.tasks.services.map_request_to_filter"
    ) as mock_map_request_to_filter, patch(
        "annotation.tasks.services.remove_additional_filters"
    ) as mock_remove_additional_filters, patch(
        "annotation.tasks.services.get_files_by_request"
    ) as mock_get_files_by_request, patch(
        "annotation.tasks.services.get_jobs_by_name"
    ) as mock_get_jobs_by_name, patch(
        "annotation.tasks.services.form_query"
    ) as mock_form_query, patch(
        "annotation.tasks.services.paginate"
    ) as mock_paginate:
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_map_request_to_filter.return_value = {
            "filters": [],
            "sorting": [],
        }
        mock_remove_additional_filters.return_value = additional_filters
        mock_get_files_by_request.return_value = files_by_name
        mock_get_jobs_by_name.return_value = jobs_by_name
        mock_query.filter.return_value = mock_query
        mock_form_query.return_value = (MagicMock(), MagicMock())
        mock_paginate.return_value = ([MagicMock()], MagicMock())
        result = services.filter_tasks_db(mock_session, request, tenant, token)
        assert len(result[0][0]) == len(expected_result[0])
        assert result[1] == expected_result[1]
        assert result[2] == expected_result[2]


@pytest.mark.parametrize(
    ("additional_filters"),
    (({"file_name": ["file1"]}), ({"job_name": ["job1"]})),
)
def test_filter_tasks_db_no_files_or_jobs(
    mock_session: Mock,
    additional_filters: Dict[str, List[str]],
):
    files_by_name = {}
    jobs_by_name = {}
    expected_result = ([], {}, {})
    request = TaskFilter()
    tenant = "test_tenant"
    token = "test_token"
    with patch(
        "annotation.tasks.services.map_request_to_filter",
        return_value={"filters": [], "sorting": []},
    ), patch(
        "annotation.tasks.services.remove_additional_filters",
        return_value=additional_filters,
    ), patch(
        "annotation.tasks.services.get_files_by_request",
        return_value=files_by_name,
    ), patch(
        "annotation.tasks.services.get_jobs_by_name", return_value=jobs_by_name
    ), patch(
        "annotation.tasks.services.form_query",
        return_value=(MagicMock(), MagicMock()),
    ), patch(
        "annotation.tasks.services.paginate",
        return_value=([MagicMock()], MagicMock()),
    ):
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        result = services.filter_tasks_db(mock_session, request, tenant, token)
        assert len(result[0]) == 2
        assert result[1] == expected_result[1]
        assert result[2] == expected_result[2]


@pytest.mark.parametrize(
    ("tasks", "job_id", "expected_user_ids", "expected_inserted_tasks"),
    (
        (
            # Test case 1: Non-empty tasks
            [
                {"user_id": 1, "file_id": 123, "pages": {1, 2}},
                {"user_id": 2, "file_id": 456, "pages": {3}},
            ],
            1,
            {1, 2},
            [  # Simulating rows returned after insertion
                {"id": 101, "user_id": 1, "file_id": 123, "pages": {1, 2}},
                {"id": 102, "user_id": 2, "file_id": 456, "pages": {3}},
            ],
        ),
        (
            # Test case 2: Empty tasks
            [],
            1,
            set(),
            None,  # No operations should occur, and None is returned
        ),
    ),
)
def test_create_tasks(
    mock_session: Mock,
    tasks: List[Dict[str, Union[int, Set[int]]]],
    job_id: int,
    expected_user_ids: Set[int],
    expected_inserted_tasks: List[Dict[str, Union[int, Set[int]]]],
):
    with patch("annotation.tasks.services.insert") as mock_insert, patch(
        "annotation.tasks.services.update_files"
    ) as mock_update_files, patch(
        "annotation.tasks.services.update_user_overall_load"
    ) as mock_update_user_overall_load:

        mock_execute_result = Mock()
        if tasks:
            mock_execute_result.mappings.return_value.all.return_value = (
                expected_inserted_tasks
            )
            mock_session.execute.return_value = mock_execute_result

        inserted_tasks = services.create_tasks(mock_session, tasks, job_id)

        if tasks:

            mock_insert.assert_called_once_with(ManualAnnotationTask)
            mock_session.execute.assert_called_once()
            mock_execute_result.mappings.return_value.all.assert_called_once()

            assert inserted_tasks == expected_inserted_tasks

            mock_update_files.assert_called_once_with(
                mock_session, tasks, job_id
            )

            mock_update_user_overall_load.assert_has_calls(
                [call(mock_session, user_id) for user_id in expected_user_ids],
                any_order=True,
            )
        else:

            mock_insert.assert_not_called()
            mock_session.execute.assert_not_called()
            mock_update_files.assert_not_called()
            mock_update_user_overall_load.assert_not_called()

            assert inserted_tasks is None


def test_update_task_status_ready(mock_session: Mock, create_task: Mock):
    task = ManualAnnotationTask(status=TaskStatusEnumSchema.ready)
    services.update_task_status(mock_session, task)
    assert task.status == TaskStatusEnumSchema.in_progress
    mock_session.add.assert_called_once_with(task)
    mock_session.commit.assert_called_once()


@pytest.mark.parametrize(
    ("status", "expected_message"),
    (
        (TaskStatusEnumSchema.pending, "Job is not started yet"),
        (TaskStatusEnumSchema.finished, "Task is already finished"),
    ),
)
def test_update_task_status_error(
    mock_session: Mock,
    create_task: Mock,
    status: TaskStatusEnumSchema,
    expected_message: str,
):
    task = create_task(status)
    with pytest.raises(FieldConstraintError, match=f".*{expected_message}.*"):
        services.update_task_status(mock_session, task)


def test_finish_validation_task(mock_session: MagicMock, create_task: Mock):
    mock_task = create_task(TaskStatusEnumSchema.ready)
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.with_for_update.return_value = mock_query
    mock_query.update.return_value = None
    services.finish_validation_task(mock_session, mock_task)
    mock_session.query.assert_called_once_with(ManualAnnotationTask)
    mock_query.with_for_update.assert_called_once()
    mock_query.update.assert_called_once_with(
        {ManualAnnotationTask.status: TaskStatusEnumSchema.finished},
        synchronize_session="fetch",
    )
    mock_session.commit.assert_called_once()


def test_count_annotation_tasks(mock_session: Mock, create_task: Mock):
    mock_task = create_task(TaskStatusEnumSchema.ready)
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 5
    result = services.count_annotation_tasks(mock_session, mock_task)
    mock_session.query.assert_called_once_with(ManualAnnotationTask)
    mock_query.filter.assert_called_once()
    mock_query.count.assert_called_once()
    assert result == 5


def test_get_task_revisions(
    mock_session: Mock, mock_task_revisions: AnnotatedDoc
):
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [mock_task_revisions]
    result = services.get_task_revisions(
        mock_session,
        tenant="test_tenant",
        job_id=1,
        task_id=1,
        file_id=1,
        task_pages=[1],
    )
    mock_session.query.assert_called_once_with(AnnotatedDoc)
    mock_query.all.assert_called_once()
    assert len(result) == 1
    assert result[0].pages == {"1": ["data1"]}
    assert result[0].failed_validation_pages == [1]
    assert result[0].validated == [1]


def test_get_task_info(mock_session: Mock, create_task: Mock):
    mock_task = create_task(TaskStatusEnumSchema.ready)
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_task
    result = services.get_task_info(
        mock_session, task_id=1, tenant="test_tenant"
    )
    mock_session.query.assert_called_once_with(ManualAnnotationTask)
    mock_query.first.assert_called_once()
    assert result == mock_task


def test_unblock_validation_tasks(
    mock_session: Mock,
    mock_task: ManualAnnotationTask,
):
    mock_unblocked_tasks = MagicMock()
    mock_session.query.return_value.filter.return_value = mock_unblocked_tasks
    mock_unblocked_tasks.all.return_value = [mock_task]
    result = services.unblock_validation_tasks(
        mock_session, mock_task, annotated_file_pages=[1, 2, 3]
    )
    mock_session.query.assert_called_once_with(ManualAnnotationTask)
    mock_session.query.return_value.filter.assert_called_once()
    mock_unblocked_tasks.update.assert_called_once_with(
        {"status": TaskStatusEnumSchema.ready},
        synchronize_session=False,
    )
    assert result == [mock_task]


def test_get_task_stats_by_id(mock_session: Mock):
    mock_stats = AnnotationStatistics()
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = mock_stats
    result = services.get_task_stats_by_id(mock_session, task_id=1)
    mock_session.query.assert_called_once_with(AnnotationStatistics)
    mock_query.filter.assert_called_once()
    mock_query.filter.return_value.first.assert_called_once()
    assert result == mock_stats


def test_add_task_stats_record_existing_stats(mock_session: Mock):
    task_id = 1
    mock_stats_input = AnnotationStatisticsInputSchema(
        event_type=AnnotationStatisticsEventEnumSchema.opened
    )
    mock_stats_db = AnnotationStatistics(updated=datetime.utcnow())
    with patch(
        "annotation.tasks.services.get_task_stats_by_id",
        return_value=mock_stats_db,
    ) as mock_get_task_stats_by_id:
        result = services.add_task_stats_record(
            mock_session, task_id, mock_stats_input
        )
        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        mock_session.add.assert_called_once_with(mock_stats_db)
        mock_session.commit.assert_called_once()
        assert result == mock_stats_db


def test_add_task_stats_record(mock_session: Mock):
    task_id = 1
    mock_stats_input = AnnotationStatisticsInputSchema(
        event_type=AnnotationStatisticsEventEnumSchema.closed
    )
    with patch(
        "annotation.tasks.services.get_task_stats_by_id", return_value=None
    ) as mock_get_task_stats_by_id:
        with pytest.raises(CheckFieldError):
            services.add_task_stats_record(
                mock_session, task_id, mock_stats_input
            )
        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


def test_add_task_stats_record_setattr(mock_session: Mock):
    task_id = 1
    mock_stats_input = AnnotationStatisticsInputSchema(
        event_type=AnnotationStatisticsEventEnumSchema.opened,
        additional_data={
            "field1": "new_value1",
            "field2": "new_value2",
        },
    )
    mock_stats_db = AnnotationStatistics()
    with patch(
        "annotation.tasks.services.get_task_stats_by_id",
        return_value=mock_stats_db,
    ) as mock_get_task_stats_by_id:
        result = services.add_task_stats_record(
            mock_session, task_id, mock_stats_input
        )
        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        assert mock_stats_db.updated is not None
        mock_session.add.assert_called_once_with(mock_stats_db)
        mock_session.commit.assert_called_once()
        assert result == mock_stats_db


def test_add_task_stats_record_create_new(mock_session: Mock):
    task_id = 1
    mock_stats_input = AnnotationStatisticsInputSchema(
        event_type=AnnotationStatisticsEventEnumSchema.opened,
        additional_data={
            "field1": "value1",
            "field2": "value2",
        },
    )
    mock_stats_db = AnnotationStatistics()
    with patch(
        "annotation.tasks.services.get_task_stats_by_id", return_value=None
    ) as mock_get_task_stats_by_id, patch(
        "annotation.tasks.services.AnnotationStatistics",
        return_value=mock_stats_db,
    ):
        result = services.add_task_stats_record(
            mock_session, task_id, mock_stats_input
        )
        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        mock_session.add.assert_called_once_with(mock_stats_db)
        mock_session.commit.assert_called_once()
        assert result == mock_stats_db


def test_evaluate_agreement_score(
    mock_session: Mock, mock_task: Mock, mock_tenant_data: Mock
):
    with patch(
        "annotation.tasks.services.get_file_path_and_bucket",
        return_value=(
            "mock_s3_file_path",
            "mock_s3_file_bucket",
        ),
    ) as mock_get_file_path_and_bucket, patch(
        "annotation.tasks.services.get_agreement_score"
    ) as mock_get_agreement_score, patch(
        "annotation.tasks.services.compare_agreement_scores",
        return_value=AgreementScoreComparingResult(
            agreement_score_reached=False,
            annotator_id=uuid.uuid4(),
            job_id=1,
            task_id=1,
            agreement_score=[ResponseScore(task_id=1, agreement_score=0.1)],
            task_metrics=[
                TaskMetric(task_from_id=1, task_to_id=2, metric_score=0.1)
            ],
        ),
    ) as mock_compare_agreement_scores:
        mock_agreement_score_response = [
            AgreementScoreServiceResponse(
                agreement_score_reached=True,
                annotator_id=uuid.uuid4(),
                job_id=1,
                task_id=1,
                agreement_score=[
                    ResponseScore(task_id=1, agreement_score=0.1)
                ],
                task_metrics=[
                    TaskMetric(task_from_id=1, task_to_id=2, metric_score=0.1)
                ],
            )
        ]
        mock_get_agreement_score.return_value = mock_agreement_score_response
        mock_session.query().all.return_value = [mock_task]
        services.evaluate_agreement_score(
            db=mock_session,
            task=mock_task,
            tenant="mock_tenant",
            token=mock_tenant_data,
        )
        mock_get_file_path_and_bucket.assert_called_once_with(
            mock_task.file_id, "mock_tenant", mock_tenant_data.token
        )
        mock_compare_agreement_scores.assert_called_once_with(
            mock_agreement_score_response, services.AGREEMENT_SCORE_MIN_MATCH
        )
        mock_get_agreement_score.assert_called_once_with(
            agreement_scores_input=[], tenant="mock_tenant", token="mock_token"
        )


def test_get_unique_scores(response_scores):
    unique_scores = set()
    task_id = 1
    services.get_unique_scores(task_id, response_scores, unique_scores)
    expected_scores = {
        services._MetricScoreTuple(task_from=1, task_to=2, score=0.9),
        services._MetricScoreTuple(task_from=1, task_to=3, score=0.7),
    }
    assert unique_scores == expected_scores


def test_compare_agreement_scores_all_above_min_match(
    mock_agreement_score_response: Mock,
    mock_parse_obj_as: Mock,
    mock_get_unique_scores: Mock,
    mock_task_metric: Mock,
    mock_agreement_score_comparing_result: Mock,
):
    min_match = 0.8
    mock_parse_obj_as.return_value = [
        ResponseScore(task_id=1, agreement_score=0.2)
    ]

    def task_metric_side_effect(task_from_id, task_to_id, metric_score):
        mock_task_metric_instance = TaskMetric(
            task_from_id=task_from_id,
            task_to_id=task_to_id,
            metric_score=metric_score,
        )
        return mock_task_metric_instance

    mock_task_metric.side_effect = task_metric_side_effect
    mock_agreement_score_comparing_result.return_value = (
        AgreementScoreComparingResult(
            agreement_score_reached=True,
            task_metrics=[
                mock_task_metric(1, 2, 0.95),
                mock_task_metric(1, 3, 0.8),
                mock_task_metric(2, 3, 0.85),
            ],
        )
    )
    result = services.compare_agreement_scores(
        mock_agreement_score_response, min_match
    )
    assert result.agreement_score_reached


def test_compare_agreement_scores_some_below_min_match(
    mock_agreement_score_response: Mock,
    mock_parse_obj_as: Mock,
    mock_get_unique_scores: Mock,
    mock_task_metric: Mock,
    mock_agreement_score_comparing_result: Mock,
):
    min_match = 0.9
    mock_parse_obj_as.return_value = [
        ResponseScore(task_id=1, agreement_score=0.2)
    ]

    def task_metric_side_effect(task_from_id, task_to_id, metric_score):
        mock_task_metric_instance = TaskMetric(
            task_from_id=task_from_id,
            task_to_id=task_to_id,
            metric_score=metric_score,
        )
        return mock_task_metric_instance

    mock_task_metric.side_effect = task_metric_side_effect
    mock_agreement_score_comparing_result.return_value = (
        AgreementScoreComparingResult(
            agreement_score_reached=False,
            task_metrics=[mock_task_metric(1, 2, 0.95)],
        )
    )
    result = services.compare_agreement_scores(
        mock_agreement_score_response, min_match
    )
    assert not result.agreement_score_reached


def test_compare_agreement_scores_empty_response(
    mock_parse_obj_as: Mock,
    mock_get_unique_scores: Mock,
    mock_task_metric: Mock,
    mock_agreement_score_comparing_result: Mock,
):
    min_match = 0.5
    mock_parse_obj_as.return_value = []
    mock_task_metric.return_value = TaskMetric(
        task_from_id=1, task_to_id=2, metric_score=0.5
    )
    mock_agreement_score_comparing_result.return_value = (
        AgreementScoreComparingResult(
            agreement_score_reached=False,
            task_metrics=[],
        )
    )
    result = services.compare_agreement_scores([], min_match)
    assert not result.agreement_score_reached
    assert result.task_metrics == []


def test_save_agreement_metrics(mock_session: Mock):
    agreement_score = AgreementScoreComparingResult(
        agreement_score_reached=True, task_metrics=[]
    )
    services.save_agreement_metrics(mock_session, agreement_score)
    mock_session.bulk_save_objects.assert_called_once_with([])
    mock_session.commit.assert_called_once()


def test_get_accum_annotations():
    with patch("annotation.tasks.services.Session") as mock_session, patch(
        "annotation.tasks.services.accumulate_pages_info",
        return_value=(
            None,
            None,
            [1, 2, 3],
            None,
            None,
            MagicMock(),
        ),
    ) as mock_accumulate_pages_info, patch(
        "annotation.tasks.services.construct_particular_rev_response"
    ) as mock_construct_particular_rev_response:
        annotation_task = ManualAnnotationTask(id=2, job_id=1, file_id=3)
        expected_revisions = AnnotatedDoc()
        mock_query = mock_session.query.return_value
        mock_query = mock_query.filter.return_value
        mock_query = mock_query.order_by.return_value
        mock_query.all.return_value = expected_revisions
        mock_accumulate_pages_info.return_value[5].pages = [1, 2, 3]
        mock_construct_particular_rev_response.return_value = (
            ParticularRevisionSchema(
                revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                user=uuid.uuid4(),
                pipeline=1,
                date=datetime(2024, 10, 19, 1, 1, 1),
                pages=[PageSchema(page_num=1, size={}, objs=[])],
            )
        )
        result = services.get_accum_annotations(
            db=mock_session,
            x_current_tenant="tenant_1",
            annotation_task=annotation_task,
        )
        mock_accumulate_pages_info.assert_called_once()
        mock_construct_particular_rev_response.assert_called_once()
        assert result == mock_construct_particular_rev_response.return_value


def test_get_accum_annotations_no_revisions(mock_session: Mock):
    with patch(
        "annotation.tasks.services.accumulate_pages_info"
    ) as mock_accumulate_pages_info, patch(
        "annotation.tasks.services.construct_particular_rev_response"
    ) as mock_construct_particular_rev_response:
        annotation_task = ManualAnnotationTask(id=2, job_id=1, file_id=3)
        mock_query = mock_session.query.return_value
        mock_query = mock_query.filter.return_value
        mock_query = mock_query.order_by.return_value
        mock_query.all.return_value = []
        result = services.get_accum_annotations(
            db=mock_session,
            x_current_tenant="tenant_1",
            annotation_task=annotation_task,
        )
        mock_accumulate_pages_info.assert_not_called()
        mock_construct_particular_rev_response.assert_not_called()
        assert result is None


def test_get_accum_annotations_no_required_revision(mock_session: Mock):
    with patch(
        "annotation.tasks.services.accumulate_pages_info",
        return_value=(
            None,
            None,
            [1, 2, 3],
            None,
            None,
            None,
        ),
    ) as mock_accumulate_pages_info, patch(
        "annotation.tasks.services.construct_particular_rev_response"
    ) as mock_construct_particular_rev_response:
        annotation_task = ManualAnnotationTask(id=2, job_id=1, file_id=3)
        expected_revisions = AnnotatedDoc()
        mock_query = mock_session.query.return_value
        mock_query = mock_query.filter.return_value
        mock_query = mock_query.order_by.return_value
        mock_query.all.return_value = expected_revisions
        result = services.get_accum_annotations(
            db=mock_session,
            x_current_tenant="tenant_1",
            annotation_task=annotation_task,
        )
        mock_accumulate_pages_info.assert_called_once()
        mock_construct_particular_rev_response.assert_not_called()
        assert result is None


def test_remove_unnecessary_attributes():
    categories = {"category1", "category2"}
    page_annotations = PageSchema(page_num=1, size={}, objs=[])
    page_annotations.size = "A4"
    page_annotations.objs = [
        {
            "type": "text",
            "data": {
                "tokens": [
                    {
                        "id": 1,
                        "text": "Sample",
                        "x": 0,
                        "y": 0,
                        "width": 100,
                        "height": 50,
                        "extra": "unnecessary",
                    },
                    {
                        "id": 2,
                        "text": "Another",
                        "x": 10,
                        "y": 20,
                        "width": 200,
                        "height": 100,
                    },
                ],
                "dataAttributes": ["attr1", "attr2"],
            },
        },
        {"type": "image", "data": {"tokens": []}},
    ]

    expected_result = {
        "size": "A4",
        "objects": [
            {
                "type": "text",
                "data": {
                    "tokens": [
                        {
                            "id": 1,
                            "text": "Sample",
                            "x": 0,
                            "y": 0,
                            "width": 100,
                            "height": 50,
                        },
                        {
                            "id": 2,
                            "text": "Another",
                            "x": 10,
                            "y": 20,
                            "width": 200,
                            "height": 100,
                        },
                    ],
                    "dataAttributes": ["attr1", "attr2"],
                },
            },
            {"type": "image", "data": {"tokens": []}},
        ],
        "categories": categories,
    }
    result = services.remove_unnecessary_attributes(
        categories, page_annotations
    )
    assert result == expected_result


@pytest.mark.parametrize(
    (
        "annotation_tasks",
        "get_accum_annotations_return_value",
        "expected_result",
    ),
    (
        (
            [ManualAnnotationTask()],
            None,
            {},
        ),
        (
            [ManualAnnotationTask()],
            ParticularRevisionSchema(
                revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                user=uuid.uuid4(),
                pipeline=1,
                date=datetime(2021, 10, 19, 1, 1, 1),
                pages=[
                    PageSchema(
                        page_num=1,
                        size={},
                        objs=[],
                        pages=[MagicMock()],
                    )
                ],
                validated=[2],
                failed_validation_pages=[],
                categories={"1", "2"},
                links_json=[
                    {"to": 2, "category": "my_category", "type": "directional"}
                ],
            ),
            {1: {0: {"size": "A4", "objects": []}}},
        ),
    ),
)
def test_load_annotations(
    mock_session: Mock,
    annotation_tasks: List[ManualAnnotationTask],
    get_accum_annotations_return_value: Optional[ParticularRevisionSchema],
    expected_result: Dict[int, Any],
):
    with patch(
        "annotation.tasks.services.get_accum_annotations",
        return_value=get_accum_annotations_return_value,
    ) as mock_get_accum_annotations, patch(
        "annotation.tasks.services.remove_unnecessary_attributes",
        return_value={
            "size": "A4",
            "objects": [],
        },
    ):
        mock_tenant = "tenant_1"
        result = services.load_annotations(
            db=mock_session,
            x_current_tenant=mock_tenant,
            annotation_tasks=annotation_tasks,
        )
        assert result == expected_result
        mock_get_accum_annotations.assert_called_once_with(
            mock_session,
            mock_tenant,
            annotation_tasks[0],
        )


@pytest.mark.parametrize(
    ("old_id", "id_mapping", "expected_result"),
    (
        (1, {(1, 2, 3): 100}, 100),
        (4, {(1, 2, 3): 100, (4, 5, 6): 200}, 200),
        (7, {(1, 2, 3): 100, (4, 5, 6): 200}, None),
        (1, {}, None),
    ),
)
def test_get_new_id(
    old_id: int,
    id_mapping: Dict[Tuple[int, ...], int],
    expected_result: Optional[int],
):
    result = services.get_new_id(old_id, id_mapping)
    assert result == expected_result


@pytest.mark.parametrize(
    ("old_id", "id_mapping", "expected_result"),
    (
        (1, {(1, 2, 3): 100}, (1, 2, 3)),
        (4, {(1, 2, 3): 100, (4, 5, 6): 200}, (4, 5, 6)),
        (7, {(1, 2, 3): 100, (4, 5, 6): 200}, ()),
        (1, {}, ()),
    ),
)
def test_get_common_ids(
    old_id: int,
    id_mapping: Dict[Tuple[int, ...], int],
    expected_result: Tuple[int, ...],
):
    result = services.get_common_ids(old_id, id_mapping)
    assert result == expected_result


@pytest.mark.parametrize(
    (
        "common_objs_ids",
        "all_tasks_objs",
        "id_mapping",
        "expected_links",
        "expected_children",
    ),
    (
        (
            (1, 2),
            {
                1: {"links": [{"to": 2}], "children": [3]},
                2: {"links": [{"to": 3}], "children": []},
            },
            {(2,): 200, (3,): 300},
            [[{"to": 2}], [{"to": 3}]],
            [[3], []],
        ),
        (
            (1,),
            {1: {"links": [{"to": 2}], "children": []}},
            {(2,): 200},
            [[{"to": 2}]],
            [[]],
        ),
        ((), {}, {}, [], []),
    ),
)
def test_get_links_and_children(
    common_objs_ids: Tuple[int, ...],
    all_tasks_objs: Dict[int, Any],
    id_mapping: Dict[Tuple[int], int],
    expected_links: List[List[Dict[str, int]]],
    expected_children: List[List[int]],
):
    with patch("annotation.tasks.services.get_new_id") as mock_get_new_id:
        mock_get_new_id.side_effect = lambda old_id, _: (
            old_id if old_id in [2, 3] else None
        )
        result_links, result_children = services.get_links_and_children(
            common_objs_ids, all_tasks_objs, id_mapping
        )
        assert result_links == expected_links
        assert result_children == expected_children


@pytest.mark.parametrize(
    ("items", "expected"),
    (
        (
            [
                [{"a": 1, "b": 2, "c": 3}, {"d": 4}, {"e": 5}],
                [{"d": 4}, {"f": 6}],
                [{"d": 4}, {"g": 7}],
            ],
            [{"d": 4}],
        ),
        (
            [
                [{"a": 1}],
                [],
                [{"b": 2}],
            ],
            [],
        ),
        (
            [
                [{"a": 1}, {"b": 2}],
            ],
            [{"a": 1}, {"b": 2}],
        ),
        ([], []),
    ),
)
def test_get_common_values(
    items: List[List[Dict[str, int]]],
    expected: List[Dict[str, int]],
):
    assert services.get_common_values(items) == expected


@pytest.mark.parametrize(
    ("old_id", "id_mapping", "expected_id"),
    (
        (1, {(1,): 101}, 101),
        (2, {(2,): 102}, 102),
        (3, {(3,): 103}, 103),
    ),
)
def test_change_ids_get_new_id(
    old_id: int, id_mapping: Dict[Tuple[int], int], expected_id: int
):
    mock_get_new_id = MagicMock(
        side_effect=lambda old_id, _: id_mapping.get((old_id,), old_id)
    )
    with patch("annotation.tasks.services.get_new_id", mock_get_new_id):
        result = services.get_new_id(old_id, id_mapping)
        assert result == expected_id
    mock_get_new_id.assert_called_with(old_id, id_mapping)


@pytest.mark.parametrize(
    ("all_tasks_objs", "doc_objs", "id_mapping", "expected_ids"),
    (
        (
            {
                "task1": {"objects": [{"id": 1}, {"id": 2}]},
                "task2": {"objects": [{"id": 3}, {"id": 4}]},
            },
            {
                "doc1": {
                    "objects": [
                        {"id": 1, "links": [2], "children": [3]},
                        {"id": 2},
                        {"id": 3},
                    ]
                }
            },
            {(1,): 101, (2,): 102, (3,): 103},
            [101, 102, 103],
        ),
    ),
)
def test_change_ids_basic(
    all_tasks_objs: Dict[str, Any],
    doc_objs: Dict[str, Dict[str, Any]],
    id_mapping: Dict[Tuple[int], int],
    expected_ids: List[int],
):
    with patch(
        "annotation.tasks.services.get_links_and_children",
        return_value=([{"test1": "test"}], [[1]]),
    ):
        services.change_ids(all_tasks_objs, doc_objs, id_mapping)
        for i, obj in enumerate(doc_objs["doc1"]["objects"]):
            assert obj["id"] == expected_ids[i]


def test_remove_ids():
    task_obj = {
        "id": 1,
        "name": "Task 1",
        "description": "This is a task.",
        "links": [2, 3],
        "children": [4, 5],
        "extra_info": "Some extra info",
    }
    expected_result = {
        "name": "Task 1",
        "description": "This is a task.",
        "extra_info": "Some extra info",
    }
    result = services.remove_ids(task_obj)
    assert result == expected_result
    assert "id" not in result
    assert "links" not in result
    assert "children" not in result


def test_find_common_objs(setup_data: Dict[int, Any]):
    task_data, all_tasks = setup_data
    expected_common_objs = [
        {"id": 1, "name": "Object A", "value": "Some Value", "links": [2]},
        {
            "id": 2,
            "name": "Object B",
            "value": "Another Value",
        },
    ]
    expected_same_ids = {1: ["1"], 2: ["2"]}
    result_common_objs, result_same_ids = services.find_common_objs(
        task_data, all_tasks
    )
    assert result_common_objs == expected_common_objs
    assert result_same_ids == expected_same_ids


def test_find_common_objs_no_common_objects():
    task_data = {
        "objects": [{"id": 3, "name": "Object D", "value": "Unique Value"}]
    }
    all_tasks = {
        1: [({"name": "Object A", "value": "Some Value"}, "1")],
        2: [({"name": "Object B", "value": "Another Value"}, "2")],
    }
    expected_common_objs = []
    expected_same_ids = {}
    result_common_objs, result_same_ids = services.find_common_objs(
        task_data, all_tasks
    )
    assert result_common_objs == expected_common_objs
    assert result_same_ids == expected_same_ids


def test_find_common_objs_empty_data():
    task_data = {"objects": []}
    all_tasks = {}
    expected_common_objs = []
    expected_same_ids = {}
    result_common_objs, result_same_ids = services.find_common_objs(
        task_data, all_tasks
    )
    assert result_common_objs == expected_common_objs
    assert result_same_ids == expected_same_ids


def test_get_tasks_without_ids_empty():
    assert services.get_tasks_without_ids({}) == {}


def test_get_tasks_without_ids_with_task_data():
    tasks = {
        1: {
            "objects": [
                {
                    "id": "1",
                    "name": "Task 1",
                    "details": {"id": "a1", "info": "Details 1"},
                },
                {"id": "2", "name": "Task 2"},
            ]
        }
    }
    expected = {
        1: [
            (
                {
                    "name": "Task 1",
                    "details": {"id": "a1", "info": "Details 1"},
                },
                "1",
            ),
            ({"name": "Task 2"}, "2"),
        ]
    }
    assert services.get_tasks_without_ids(tasks) == expected


def test_get_tasks_without_ids_with_nested_info():
    tasks = {
        2: {
            "objects": [
                {
                    "id": "3",
                    "info": {"id": "b3", "value": "Nested Value"},
                },
            ]
        }
    }
    expected = {2: [({"info": {"id": "b3", "value": "Nested Value"}}, "3")]}
    assert services.get_tasks_without_ids(tasks) == expected


def test_get_tasks_without_ids_with_multiple_task_types():
    tasks = {
        3: {
            "objects": [
                {"id": "4", "name": "Task 4"},
                {"id": "5", "status": "Complete"},
            ]
        },
        4: {
            "objects": [
                {"id": "6", "description": "Task 6"},
            ]
        },
    }
    expected = {
        3: [({"name": "Task 4"}, "4"), ({"status": "Complete"}, "5")],
        4: [({"description": "Task 6"}, "6")],
    }
    assert services.get_tasks_without_ids(tasks) == expected


def test_create_validation_revisions_successful(
    mock_session: Mock,
    mock_get_file_path_and_bucket: Mock,
    mock_construct_annotated_pages: PageSchema,
    mock_construct_annotated_doc: Mock,
    mock_update_task_status: Mock,
    mock_logger_exception: Mock,
):
    x_current_tenant = "tenant_1"
    token = MagicMock(token="fake_token")
    job_id = 123
    user_id = uuid.uuid4()
    validation_tasks = [
        ManualAnnotationTask(file_id=1, pages={1}, user_id=user_id, id=10)
    ]
    services.create_validation_revisions(
        mock_session, x_current_tenant, token, job_id, validation_tasks
    )
    mock_get_file_path_and_bucket.assert_called_once_with(
        1, x_current_tenant, token.token
    )
    mock_logger_exception.assert_not_called()


def test_create_validation_revisions_multiple_tasks(
    mock_session: Mock,
    mock_get_file_path_and_bucket: Mock,
    mock_construct_annotated_pages: PageSchema,
    mock_construct_annotated_doc: Mock,
    mock_update_task_status: Mock,
    mock_logger_exception: Mock,
):
    x_current_tenant = "tenant_1"
    token = MagicMock(token="fake_token")
    job_id = 123
    validation_tasks = [
        ManualAnnotationTask(
            file_id=1, pages={1, 2}, user_id=uuid.uuid4(), id=10
        ),
        ManualAnnotationTask(
            file_id=2, pages={3}, user_id=uuid.uuid4(), id=11
        ),
    ]
    with patch(
        "annotation.tasks.services.construct_annotated_pages",
        return_value=(
            [
                PageSchema(
                    page_num=10,
                    size={"width": 10.2, "height": 123.34},
                    objs=[
                        {
                            "id": 2,
                        }
                    ],
                ),
            ],
            set(["tasks1", "tasks2"]),
        ),
    ):
        services.create_validation_revisions(
            mock_session, x_current_tenant, token, job_id, validation_tasks
        )

        assert mock_get_file_path_and_bucket.call_count == 2
        mock_logger_exception.assert_not_called()


def test_create_validation_revisions_multiple_tasks_value_error(
    mock_session: Mock,
    mock_get_file_path_and_bucket: Mock,
    mock_construct_annotated_pages: PageSchema,
    mock_construct_annotated_doc: Mock,
    mock_update_task_status: Mock,
    mock_logger_exception: Mock,
):
    x_current_tenant = "tenant_1"
    token = MagicMock(token="fake_token")
    job_id = 123
    validation_tasks = [
        ManualAnnotationTask(
            file_id=1, pages={1, 2}, user_id=uuid.uuid4(), id=10
        ),
        ManualAnnotationTask(
            file_id=2, pages={3}, user_id=uuid.uuid4(), id=11
        ),
    ]
    mock_construct_annotated_doc.side_effect = ValueError(
        "Simulation of a fault"
    )
    with patch(
        "annotation.tasks.services.construct_annotated_pages",
        return_value=(
            [
                PageSchema(
                    page_num=10,
                    size={"width": 10.2, "height": 123.34},
                    objs=[
                        {
                            "id": 2,
                        }
                    ],
                ),
            ],
            set(["tasks1", "tasks2"]),
        ),
    ):
        services.create_validation_revisions(
            mock_session, x_current_tenant, token, job_id, validation_tasks
        )
    assert mock_get_file_path_and_bucket.call_count == 2
    mock_logger_exception.assert_called_with(
        "Cannot save first validation revision."
    )
    mock_update_task_status.assert_not_called()


def test_construct_annotated_pages(mock_session: Mock):
    x_current_tenant = "tenant_1"
    with patch(
        "annotation.tasks.services.PageSchema",
        return_value=PageSchema(page_num=1, size={}, objs=[]),
    ), patch("annotation.tasks.services.load_annotations", return_value={}):
        pages, categories = services.construct_annotated_pages(
            mock_session, x_current_tenant, []
        )
        assert not pages
        assert not categories


def test_construct_annotated_pages_common_objs(mock_session: Mock):
    x_current_tenant = "tenant_1"
    annotation_tasks = [
        ManualAnnotationTask(file_id=1, pages={1}, user_id=1, id=10),
        ManualAnnotationTask(file_id=2, pages={1}, user_id=2, id=11),
    ]
    mock_tasks_annotations = {
        1: {
            1: {
                "size": (1000, 1000),
                "objects": [{"id": "1", "type": "rect"}],
                "categories": {"cat1"},
            },
            2: {
                "size": (1000, 1000),
                "objects": [{"id": "2", "type": "rect"}],
                "categories": {"cat1"},
            },
        },
        2: {},
    }
    expected_categories = {"cat1"}
    with patch(
        "annotation.tasks.services.load_annotations",
        return_value=mock_tasks_annotations,
    ), patch(
        "annotation.tasks.services.PageSchema",
        return_value=PageSchema(page_num=1000, size={}, objs=[]),
    ):
        _, categories = services.construct_annotated_pages(
            mock_session, x_current_tenant, annotation_tasks
        )
        assert categories == expected_categories


def test_construct_annotated_pages_no_common_categories(mock_session: Mock):
    x_current_tenant = "tenant_1"
    annotation_tasks = [
        ManualAnnotationTask(file_id=1, pages={1}, user_id=1, id=10),
    ]
    mock_tasks_annotations = {
        1: {
            1: {
                "size": (1000, 1000),
                "objects": [{"id": "1", "type": "rect"}],
                "categories": {"cat1"},
            },
            2: {
                "size": (1000, 1000),
                "objects": [{"id": "2", "type": "rect"}],
                "categories": {"cat2"},
            },
        },
    }
    expected_categories = set()
    with patch(
        "annotation.tasks.services.load_annotations",
        return_value=mock_tasks_annotations,
    ), patch(
        "annotation.tasks.services.PageSchema",
        return_value=PageSchema(page_num=10, size={}, objs=[]),
    ):
        _, categories = services.construct_annotated_pages(
            mock_session, x_current_tenant, annotation_tasks
        )
        assert categories == expected_categories


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


def test_lru():
    cache = services.LRU(2)
    cache[1] = "test1"
    cache[2] = "test2"
    assert cache[1] == "test1"
    assert cache[2] == "test2"


def test_lru_key_removed_due_to_capacity():
    cache = services.LRU(2)
    cache[1] = "test1"
    cache[2] = "test2"
    cache[3] = "test3"
    assert len(cache) == 2
    with pytest.raises(KeyError):
        cache[1]
