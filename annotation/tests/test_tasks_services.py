import re
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from fastapi import HTTPException
from tenant_dependency import TenantData

from annotation.errors import FieldConstraintError
from annotation.filters import TaskFilter
from annotation.models import (
    AgreementMetrics,
    AnnotatedDoc,
    File,
    ManualAnnotationTask,
)
from annotation.schemas.jobs import ValidationSchema
from annotation.schemas.tasks import (
    AgreementScoreServiceResponse,
    ManualAnnotationTaskInSchema,
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


def test_validate_task_info_invalid_task_info(mock_session: Mock):
    task_info = {"is_validation": False}
    validation_type = ValidationSchema.validation_only

    with pytest.raises(FieldConstraintError):
        services.validate_task_info(mock_session, task_info, validation_type)


@pytest.mark.parametrize("is_validation", (True, False))
def test_validate_users_info(mock_session: Mock, is_validation: bool):
    task_info = {
        "is_validation": is_validation,
        "user_id": 1,
        "job_id": 2,
    }
    mock_session.query().filter_by().first().return_value = True
    services.validate_users_info(
        mock_session, task_info, ValidationSchema.validation_only
    )
    assert mock_session.query.call_count == 2


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
    task_info = {
        "is_validation": is_validation,
        "user_id": 1,
        "job_id": 2,
    }
    mock_session.query().filter_by().first.return_value = None
    expected_error_message = (
        f"user 1 is not assigned as {validator_or_annotator} for job 2"
    )
    with pytest.raises(FieldConstraintError, match=expected_error_message):
        services.validate_users_info(
            mock_session, task_info, ValidationSchema.validation_only
        )


def test_validate_files_info(mock_session: Mock):
    task_info = {
        "file_id": 1,
        "job_id": 2,
        "pages": [1, 2, 3],
    }
    mock_file = Mock(spec=File)
    mock_file.pages_number = 3
    mock_query = mock_session.query.return_value
    mock_query.filter_by.return_value.first.return_value = mock_file
    services.validate_files_info(mock_session, task_info)
    assert mock_session.query.call_count == 1
    mock_session.query.assert_has_calls((call(File),))
    mock_query.filter_by.assert_called_once_with(file_id=1, job_id=2)


def test_validate_files_info_invalid_page_numbers(mock_session: Mock):
    task_info = {
        "file_id": 1,
        "job_id": 2,
        "pages": [1, 2, 4],
    }
    mock_file = Mock(spec=File, pages_number=3)
    mock_session.query().filter_by().first.return_value = mock_file
    expected_error_message_regex = r"pages \(\{4\}\) do not belong to file"
    with pytest.raises(
        FieldConstraintError, match=expected_error_message_regex
    ):
        services.validate_files_info(mock_session, task_info)


def test_validate_files_info_missing_file(mock_session: Mock):
    task_info = {
        "file_id": 1,
        "job_id": 2,
        "pages": [1, 2, 3],
    }
    mock_session.query().filter_by().first.return_value = None

    expected_error_message_regex = r"file with id 1 is not assigned for job 2"
    with pytest.raises(
        FieldConstraintError, match=expected_error_message_regex
    ):
        services.validate_files_info(mock_session, task_info)


def test_check_cross_annotating_pages(mock_session: Mock):
    task_info = {"user_id": 1, "file_id": 2, "job_id": 3, "pages": {4, 5}}
    existing_pages = []

    mock_query = mock_session.query.return_value
    mock_query.filter.return_value.all.return_value = [(existing_pages,)]

    services.check_cross_annotating_pages(mock_session, task_info)

    assert mock_session.query.call_count == 1
    mock_session.query.assert_has_calls((call(ManualAnnotationTask.pages),))
    mock_query.filter.assert_called_once()


def test_check_cross_annotating_pages_page_already_annotated(
    mock_session: Mock,
):
    task_info = {"user_id": 1, "file_id": 2, "job_id": 3, "pages": {4, 5}}
    existing_pages = [4, 5]
    mock_query = mock_session.query.return_value
    mock_query.filter.return_value.all.return_value = [(existing_pages,)]
    with pytest.raises(
        FieldConstraintError, match=".*tasks for this user: {4, 5}.*"
    ):
        services.check_cross_annotating_pages(mock_session, task_info)


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
    common_objs_ids: Tuple[int],
    all_tasks_objs: Dict[int, Dict[str, List[Dict[str, int]]]],
    id_mapping: Dict[Tuple[int], int],
    expected_links: List[List[Dict[str, int]]],
    expected_children: List[List[int]],
):
    with patch("annotation.tasks.services.get_new_id") as mock_get_new_id:
        mock_get_new_id.side_effect = (
            lambda old_id, _: old_id if old_id in [2, 3] else None
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
    items: List[List[Optional[Dict[str, int]]]],
    expected: List[Optional[Dict[str, int]]],
):
    assert services.get_common_values(items) == expected


@pytest.mark.parametrize(
    (
        "all_tasks_objs",
        "doc_objs",
        "id_mapping",
        "expected_ids",
        "expected_links",
        "expected_id",
        "expected_children",
    ),
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
            [101],
            [3, 1],
            [3],
        ),
        (
            {
                "task1": {"objects": [{"id": 1}, {"id": 2}, {"id": 3}]},
                "task2": {"objects": [{"id": 4}, {"id": 5}, {"id": 6}]},
            },
            {
                "doc1": {
                    "objects": [
                        {"id": 1, "links": [2], "children": [3, 4]},
                        {"id": 2},
                        {"id": 3},
                    ]
                }
            },
            {(1,): 101, (2,): 102, (3,): 103, (4,): 104},
            [101, 102, 103],
            [101],
            [3, 1],
            [101],
        ),
    ),
)
def test_change_ids(
    all_tasks_objs: Dict[str, Any],
    doc_objs: Dict[str, Dict[str, Any]],
    id_mapping: Dict[Tuple[int], int],
    expected_ids: List[int],
    expected_links: List[int],
    expected_id: List[int],
    expected_children: List[int],
):
    mock_get_new_id = MagicMock(
        side_effect=lambda old_id, _: id_mapping.get((old_id,), old_id)
    )
    mock_get_common_ids = MagicMock(
        side_effect=lambda old_id, _: [id_mapping.get((old_id,), old_id)]
    )
    mock_get_links_and_children = MagicMock(
        side_effect=lambda ids, _, __: (
            [id_mapping.get((i,), i) for i in ids],
            [id_mapping.get((i,), i) for i in ids],
        )
    )
    mock_get_common_values = MagicMock(side_effect=lambda objs: objs)

    with patch("annotation.tasks.services.get_new_id", mock_get_new_id), patch(
        "annotation.tasks.services.get_common_ids", mock_get_common_ids
    ), patch(
        "annotation.tasks.services.get_links_and_children",
        mock_get_links_and_children,
    ), patch(
        "annotation.tasks.services.get_common_values", mock_get_common_values
    ):
        services.change_ids(all_tasks_objs, doc_objs, id_mapping)
    for i, obj in enumerate(doc_objs["doc1"]["objects"]):
        assert obj["id"] == expected_ids[i]
    mock_get_new_id.assert_called_with(*(expected_id[0], id_mapping))
    mock_get_common_ids.assert_called_with(*(expected_id[1], id_mapping))
    mock_get_links_and_children.assert_called_with(
        *(expected_links, all_tasks_objs, id_mapping)
    )
    mock_get_common_values.assert_called_with(expected_links)


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
