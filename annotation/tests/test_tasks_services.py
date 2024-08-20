import re
import unittest
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock, call, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from tenant_dependency import TenantData

from annotation.errors import CheckFieldError, FieldConstraintError
from annotation.filters import TaskFilter
from annotation.jobs.services import ValidationSchema
from annotation.models import (
    AnnotatedDoc,
    AnnotationStatistics,
    File,
    ManualAnnotationTask,
)
from annotation.schemas.annotations import PageSchema, ParticularRevisionSchema
from annotation.schemas.tasks import (
    AgreementScoreComparingResult,
    AgreementScoreServiceResponse,
    AnnotationStatisticsInputSchema,
    ManualAnnotationTaskInSchema,
    ResponseScore,
    TaskMetric,
    TaskStatusEnumSchema,
)
from annotation.tasks.services import (
    AGREEMENT_SCORE_MIN_MATCH,
    _MetricScoreTuple,
    add_task_stats_record,
    change_ids,
    check_cross_annotating_pages,
    compare_agreement_scores,
    construct_annotated_pages,
    count_annotation_tasks,
    create_annotation_task,
    create_export_csv,
    create_tasks,
    create_validation_revisions,
    evaluate_agreement_score,
    filter_tasks_db,
    find_common_objs,
    finish_validation_task,
    get_accum_annotations,
    get_annotation_tasks,
    get_common_ids,
    get_common_values,
    get_file_names_by_file_ids,
    get_from_cache,
    get_links_and_children,
    get_new_id,
    get_task_info,
    get_task_revisions,
    get_task_stats_by_id,
    get_tasks_without_ids,
    get_unique_scores,
    get_user_names_by_user_ids,
    load_annotations,
    read_annotation_task,
    read_annotation_tasks,
    remove_additional_filters,
    remove_ids,
    remove_unnecessary_attributes,
    save_agreement_metrics,
    unblock_validation_tasks,
    update_task_status,
    validate_files_info,
    validate_ids_and_names,
    validate_task_info,
    validate_user_actions,
    validate_users_info,
)


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

        validate_task_info(None, task_info, validation_type)

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
            validate_task_info(db_session, task_info, validation_type)


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

        validate_users_info(
            db_session, task_info, ValidationSchema.validation_only
        )

        assert db_session.query.call_count == 2


def test_validate_users_info_cross_validation():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session, patch(
        "annotation.tasks.services.check_cross_annotating_pages"
    ) as mock_func:
        db_session = mock_session()
        task_info = {
            "is_validation": True,
            "user_id": 1,
            "job_id": 2,
        }

        validate_users_info(db_session, task_info, ValidationSchema.cross)
        mock_func.assert_called_once_with(db_session, task_info)


@pytest.mark.parametrize(
    ("is_validation", "validator_or_annotator"),
    ((True, "validator"), (False, "annotator")),
)
def test_validate_users_info_invalid_users_info(
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
            validate_users_info(
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

        validate_files_info(db_session, task_info)

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
            validate_files_info(db_session, task_info)


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
            validate_files_info(db_session, task_info)


def test_check_cross_annotating_pages():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {"user_id": 1, "file_id": 2, "job_id": 3, "pages": {4, 5}}
        existing_pages = []

        mock_query = db_session.query.return_value
        mock_query.filter.return_value.all.return_value = [(existing_pages,)]

        check_cross_annotating_pages(db_session, task_info)

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
            check_cross_annotating_pages(db_session, task_info)


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
        validate_user_actions(
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
        validate_user_actions(
            is_validation=True,
            failed=failed,
            annotated=annotated,
            not_processed=not_processed,
            annotation_user=True,
            validation_user=True,
        )
    assert re.match(expected_error_message_pattern, excinfo.value.detail)


@pytest.fixture
def mock_session():
    with patch("annotation.tasks.services.Session", spec=True) as mock_session:
        yield mock_session()


def test_create_annotation_task(mock_session: Mock):
    with patch("annotation.tasks.services.update_user_overall_load"):
        result = create_annotation_task(
            mock_session,
            ManualAnnotationTaskInSchema(
                file_id=1,
                pages={1, 2},
                job_id=2,
                user_id=uuid4(),
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

    total_objects, annotation_tasks = read_annotation_tasks(
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
    result = validate_ids_and_names(
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
        validate_ids_and_names(
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

    result = remove_additional_filters(filter_args)

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
    result = remove_additional_filters(filter_args)
    assert filter_args == expected_filters
    assert result == expected_additional_filters


def test_read_annotation_task(mock_session: Mock):
    expected_result = "task1"

    mock_query = MagicMock()
    mock_filter = MagicMock()

    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = expected_result

    result = read_annotation_task(mock_session, task_id=1, tenant="tenant_1")

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

        result = filter_tasks_db(mock_session, request, tenant, token)

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

        result = filter_tasks_db(mock_session, request, tenant, token)

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

        result = filter_tasks_db(mock_session, request, tenant, token)

        assert len(result[0]) == 2
        assert result[1] == expected_result[1]
        assert result[2] == expected_result[2]


def test_create_tasks(mock_session: Mock):
    tasks = [
        {"user_id": 1, "file_id": 123, "pages": {1, 2}},
        {"user_id": 2, "file_id": 456, "pages": {3}},
    ]
    job_id = 1
    expected_user_ids = {1, 2}
    with patch(
        "annotation.tasks.services.update_files"
    ) as mock_update_files, patch(
        "annotation.tasks.services.update_user_overall_load"
    ) as mock_update_user_overall_load:

        create_tasks(mock_session, tasks, job_id)

        mock_session.bulk_insert_mappings.assert_called_once()
        mock_update_files.assert_called_once_with(mock_session, tasks, job_id)
        mock_update_user_overall_load.assert_has_calls(
            [call(mock_session, user_id) for user_id in expected_user_ids],
            any_order=True,
        )


def test_create_tasks_with_empty_tasks(mock_session: Mock):
    tasks = []
    job_id = 1
    with patch(
        "annotation.tasks.services.update_files"
    ) as mock_update_files, patch(
        "annotation.tasks.services.update_user_overall_load"
    ) as mock_update_user_overall_load:

        create_tasks(mock_session, tasks, job_id)

        mock_session.bulk_insert_mappings.assert_called_once()
        mock_update_files.assert_called_once_with(mock_session, tasks, job_id)
        mock_update_user_overall_load.assert_not_called()


def create_task(status: TaskStatusEnumSchema) -> ManualAnnotationTask:
    task = MagicMock(spec=ManualAnnotationTask)
    task.status = status
    task.id = 1
    return task


def test_update_task_status_ready(mock_session: Mock):
    task = create_task(TaskStatusEnumSchema.ready)

    update_task_status(mock_session, task)

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
    mock_session: Mock, status: TaskStatusEnumSchema, expected_message: str
):
    task = create_task(status)
    with pytest.raises(FieldConstraintError, match=f".*{expected_message}.*"):
        update_task_status(mock_session, task)


def test_finish_validation_task(mock_session: MagicMock):
    mock_task = create_task(TaskStatusEnumSchema.ready)
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.with_for_update.return_value = mock_query
    mock_query.update.return_value = None

    finish_validation_task(mock_session, mock_task)

    mock_session.query.assert_called_once_with(ManualAnnotationTask)

    mock_query.with_for_update.assert_called_once()
    mock_query.update.assert_called_once_with(
        {ManualAnnotationTask.status: TaskStatusEnumSchema.finished},
        synchronize_session="fetch",
    )
    mock_session.commit.assert_called_once()


def test_count_annotation_tasks(mock_session: Mock):
    mock_task = create_task(TaskStatusEnumSchema.ready)
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 5

    result = count_annotation_tasks(mock_session, mock_task)

    mock_session.query.assert_called_once_with(ManualAnnotationTask)
    mock_query.filter.assert_called_once_with(
        unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY
    )
    mock_query.count.assert_called_once()

    assert result == 5


@pytest.fixture
def mock_task_revisions():
    mock_revision = MagicMock(spec=AnnotatedDoc)
    mock_revision.pages = {"1": ["data1"], "2": ["data2"]}
    mock_revision.failed_validation_pages = [1, 2]
    mock_revision.validated = [1, 2]
    yield [mock_revision]


def test_get_task_revisions(
    mock_session: Mock, mock_task_revisions: List[AnnotatedDoc]
):
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_task_revisions

    result = get_task_revisions(
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


def test_get_task_info(mock_session: Mock):
    mock_task = create_task(TaskStatusEnumSchema.ready)

    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_task

    result = get_task_info(mock_session, task_id=1, tenant="test_tenant")

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

    result = unblock_validation_tasks(
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
    mock_stats = MagicMock(spec=AnnotationStatistics)

    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = mock_stats

    result = get_task_stats_by_id(mock_session, task_id=1)

    mock_session.query.assert_called_once_with(AnnotationStatistics)
    mock_query.filter.assert_called_once()
    mock_query.filter.return_value.first.assert_called_once()

    assert result == mock_stats


def test_add_task_stats_record_existing_stats(mock_session: Mock):
    task_id = 1
    mock_stats_input = MagicMock(spec=AnnotationStatisticsInputSchema)
    mock_stats_input.event_type = "open"
    mock_stats_db = MagicMock(spec=AnnotationStatistics)
    with patch(
        "annotation.tasks.services.get_task_stats_by_id"
    ) as mock_get_task_stats_by_id:
        mock_get_task_stats_by_id.return_value = mock_stats_db

        result = add_task_stats_record(mock_session, task_id, mock_stats_input)

        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        mock_stats_db.field1 = "value1"
        mock_stats_db.field2 = "value2"
        mock_stats_db.updated = datetime.utcnow()
        mock_session.add.assert_called_once_with(mock_stats_db)
        mock_session.commit.assert_called_once()

        assert result == mock_stats_db


def test_add_task_stats_record(mock_session: Mock):
    task_id = 1
    mock_stats_input = MagicMock(spec=AnnotationStatisticsInputSchema)
    mock_stats_input.event_type = "closed"
    with patch(
        "annotation.tasks.services.get_task_stats_by_id", return_value=None
    ) as mock_get_task_stats_by_id:

        with pytest.raises(CheckFieldError):
            add_task_stats_record(mock_session, task_id, mock_stats_input)

        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


def test_add_task_stats_record_setattr(mock_session: Mock):
    task_id = 1
    mock_stats_input = MagicMock(spec=AnnotationStatisticsInputSchema)
    mock_stats_input.dict.return_value = {
        "field1": "new_value1",
        "field2": "new_value2",
    }
    mock_stats_db = MagicMock(spec=AnnotationStatistics)
    mock_stats_db.field1 = "old_value1"
    mock_stats_db.field2 = "old_value2"
    with patch(
        "annotation.tasks.services.get_task_stats_by_id",
        return_value=mock_stats_db,
    ) as mock_get_task_stats_by_id:
        result = add_task_stats_record(mock_session, task_id, mock_stats_input)

        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        assert mock_stats_db.field1 == "new_value1"
        assert mock_stats_db.field2 == "new_value2"
        assert mock_stats_db.updated is not None

        mock_session.add.assert_called_once_with(mock_stats_db)
        mock_session.commit.assert_called_once()

        assert result == mock_stats_db


def test_add_task_stats_record_create_new(mock_session: Mock):
    task_id = 1
    mock_stats_input = MagicMock(spec=AnnotationStatisticsInputSchema)
    mock_stats_input.event_type = "open"
    mock_stats_input.dict.return_value = {
        "field1": "value1",
        "field2": "value2",
    }
    mock_stats_db = MagicMock()
    with patch(
        "annotation.tasks.services.get_task_stats_by_id", return_value=None
    ) as mock_get_task_stats_by_id, patch(
        "annotation.tasks.services.AnnotationStatistics",
        return_value=mock_stats_db,
    ) as mock_annotation_statistics:
        result = add_task_stats_record(mock_session, task_id, mock_stats_input)

        mock_get_task_stats_by_id.assert_called_once_with(
            mock_session, task_id
        )
        mock_annotation_statistics.assert_called_once_with(
            task_id=task_id, **mock_stats_input.dict.return_value
        )
        mock_session.add.assert_called_once_with(mock_stats_db)
        mock_session.commit.assert_called_once()

        assert result == mock_stats_db


def test_get_from_cache():
    objs_ids = {1, 2, 3}
    cache_used = MagicMock()

    # Setting up the behavior of the __contains__ method on the mock object
    # This method is used to check if the object contains a specific key
    # side_effect returns True if the key is in the set {1, 3},
    # otherwise returns False
    cache_used.__contains__.side_effect = lambda key: key in {1, 3}

    # Setting up the behavior of the __getitem__ method on the mock object
    # This method is used to access values by key
    # side_effect returns the value from the dictionary for the given key,
    # or None if the key is not present
    cache_used.__getitem__.side_effect = {1: "name1", 3: "name3"}.get
    objs_names_from_cache, not_cached_usernames = get_from_cache(
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

        result = get_user_names_by_user_ids(user_ids, tenant, token)

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

        result = get_file_names_by_file_ids(file_ids, tenant, token)

        mock_get_from_cache.assert_called_once_with(
            objs_ids=file_ids, cache_used=mock_cache
        )

        mock_get_file_names_by_request.assert_called_once_with(
            file_ids=list(not_cached_file_ids), tenant=tenant, token=token
        )

        mock_cache.update.assert_called_once_with(file_names_from_requests)

        expected_result = {**cached_file_names, **file_names_from_requests}

        assert result == expected_result


@pytest.fixture
def mock_metric():
    metric = MagicMock()
    metric.task_from = datetime(2024, 1, 1)
    metric.task_to = datetime(2024, 2, 1)
    metric.agreement_metric = True
    yield metric


@pytest.fixture
def mock_stats(mock_task: ManualAnnotationTask, mock_metric: Mock):
    stat1 = MagicMock()
    stat1.task = mock_task
    stat1.task_id = 1
    stat1.created = datetime(2024, 1, 1, 12, 0, 0)
    stat1.updated = datetime(2024, 1, 2, 12, 0, 0)
    stat1.task.user_id = 2
    stat1.task.file_id = 3
    stat1.task.pages = [1, 2, 3]
    stat1.task.status.value = "completed"
    stat1.task.agreement_metrics = [mock_metric]

    stat2 = MagicMock()
    stat2.task = mock_task
    stat2.task_id = 2
    stat2.created = datetime(2024, 1, 3, 12, 0, 0)
    stat2.updated = datetime(2024, 1, 4, 12, 0, 0)
    stat2.task.user_id = 2
    stat2.task.file_id = 3
    stat2.task.pages = [1, 2, 3]
    stat2.task.status.value = "completed"
    stat2.task.agreement_metrics = [mock_metric]

    stat3 = MagicMock()
    stat3.task = mock_task
    stat3.task_id = 3
    stat3.created = datetime(2024, 1, 5, 12, 0, 0)
    stat3.updated = datetime(2024, 1, 6, 12, 0, 0)
    stat3.task.user_id = 2
    stat3.task.file_id = 3
    stat3.task.pages = [1, 2, 3]
    stat3.task.status.value = "completed"
    stat3.task.agreement_metrics = [mock_metric]

    yield [stat1, stat2, stat3]


@pytest.fixture
def mock_db(mock_stats):
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.filter.return_value.all.return_value = (
        mock_stats
    )
    mock_db.query.return_value = mock_query

    return mock_db


@pytest.mark.parametrize(
    ("schema", "expected_filename"),
    (
        (
            MagicMock(
                user_ids=[2],
                date_from=datetime(2024, 1, 1),
                date_to=datetime(2024, 1, 6),
            ),
            f"annotator_stats_export_{datetime.now().strftime('%Y%m%d')}.csv",
        ),
        (
            MagicMock(
                user_ids=[999],
                date_from=datetime(2024, 1, 1),
                date_to=datetime(2024, 1, 6),
            ),
            f"annotator_stats_export_{datetime.now().strftime('%Y%m%d')}.csv",
        ),
    ),
)
def test_create_export_csv(
    schema: Mock, expected_filename: str, mock_db: Mock
):
    mock_user_name = {2: "user2"}
    mock_file_name = {3: "file3"}
    with patch(
        "annotation.tasks.services.get_user_names_by_user_ids",
        return_value=mock_user_name,
    ), patch(
        "annotation.tasks.services.get_file_names_by_file_ids",
        return_value=mock_file_name,
    ), patch(
        "annotation.tasks.services.io.BytesIO"
    ), patch(
        "annotation.tasks.services.io.TextIOWrapper"
    ):

        filename, _ = create_export_csv(mock_db, schema, "tenant", "token")

        assert filename == expected_filename


@pytest.mark.parametrize(
    ("schema", "expected_filename"),
    (
        (
            MagicMock(
                user_ids=[2],
                date_from=datetime(2024, 1, 1),
                date_to=None,
            ),
            f"annotator_stats_export_{datetime.now().strftime('%Y%m%d')}.csv",
        ),
    ),
)
def test_create_export_csv_no_date_to(
    schema: Mock, expected_filename: str, mock_db: Mock
):
    mock_user_name = {2: "user2"}
    mock_file_name = {3: "file3"}
    with patch(
        "annotation.tasks.services.get_user_names_by_user_ids",
        return_value=mock_user_name,
    ), patch(
        "annotation.tasks.services.get_file_names_by_file_ids",
        return_value=mock_file_name,
    ), patch(
        "annotation.tasks.services.io.BytesIO"
    ), patch(
        "annotation.tasks.services.io.TextIOWrapper",
    ):

        filename, _ = create_export_csv(mock_db, schema, "tenant", "token")

        assert filename == expected_filename


def test_create_export_csv_no_annotation_stats(mock_db):
    schema = MagicMock(
        user_ids=[999],
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
            create_export_csv(mock_db, schema, "tenant", "token")

        assert exc_info.value.status_code == 406
        assert exc_info.value.detail == "Export data not found."


@pytest.fixture
def mock_task():
    task = MagicMock(ManualAnnotationTask)
    task.id = 1
    task.user_id = 2
    task.job_id = 10
    task.file_id = 3
    task.pages = {1, 2, 3}
    task.is_validation = False
    yield task


@pytest.fixture
def mock_tenant_data():
    mock_data = MagicMock(TenantData)
    mock_data.token = "mock_token"
    yield mock_data


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
        return_value=MagicMock(AgreementScoreComparingResult),
    ) as mock_compare_agreement_scores:

        mock_agreement_score_response = [
            MagicMock(AgreementScoreServiceResponse)
        ]
        mock_get_agreement_score.return_value = mock_agreement_score_response
        mock_session.query().all.return_value = [mock_task]
        result = evaluate_agreement_score(
            db=mock_session,
            task=mock_task,
            tenant="mock_tenant",
            token=mock_tenant_data,
        )

        mock_get_file_path_and_bucket.assert_called_once_with(
            mock_task.file_id, "mock_tenant", mock_tenant_data.token
        )

        mock_compare_agreement_scores.assert_called_once_with(
            mock_agreement_score_response, AGREEMENT_SCORE_MIN_MATCH
        )

        assert isinstance(result, AgreementScoreComparingResult)


@pytest.fixture
def response_scores():
    return [
        ResponseScore(task_id=2, agreement_score=0.9),
        ResponseScore(task_id=3, agreement_score=0.7),
        ResponseScore(task_id=2, agreement_score=0.9),
    ]


def test_get_unique_scores(response_scores):
    unique_scores = set()
    task_id = 1

    get_unique_scores(task_id, response_scores, unique_scores)

    expected_scores = {
        _MetricScoreTuple(task_from=1, task_to=2, score=0.9),
        _MetricScoreTuple(task_from=1, task_to=3, score=0.7),
    }

    assert unique_scores == expected_scores


@pytest.fixture
def mock_agreement_score_response():
    mock_response = [
        MagicMock(spec=AgreementScoreServiceResponse),
        MagicMock(spec=AgreementScoreServiceResponse),
    ]
    mock_response[0].task_id = 1
    mock_response[0].agreement_score = [
        MagicMock(spec=ResponseScore, task_id=2, agreement_score=0.95),
        MagicMock(spec=ResponseScore, task_id=3, agreement_score=0.8),
    ]
    mock_response[1].task_id = 2
    mock_response[1].agreement_score = [
        MagicMock(spec=ResponseScore, task_id=1, agreement_score=0.95),
        MagicMock(spec=ResponseScore, task_id=3, agreement_score=0.85),
    ]
    return mock_response


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


def test_compare_agreement_scores_all_above_min_match(
    mock_agreement_score_response: Mock,
    mock_parse_obj_as: Mock,
    mock_get_unique_scores: Mock,
    mock_task_metric: Mock,
    mock_agreement_score_comparing_result: Mock,
):
    min_match = 0.8
    mock_parse_obj_as.return_value = [MagicMock(spec=ResponseScore)]
    mock_task_metric.side_effect = (
        lambda task_from_id, task_to_id, metric_score: MagicMock(
            spec=TaskMetric,
            task_from_id=task_from_id,
            task_to_id=task_to_id,
            metric_score=metric_score,
        )
    )
    mock_agreement_score_comparing_result.return_value = MagicMock(
        spec=AgreementScoreComparingResult,
        agreement_score_reached=True,
        task_metrics=[
            mock_task_metric(1, 2, 0.95),
            mock_task_metric(1, 3, 0.8),
            mock_task_metric(2, 3, 0.85),
        ],
    )
    result = compare_agreement_scores(mock_agreement_score_response, min_match)
    assert result.agreement_score_reached


def test_compare_agreement_scores_some_below_min_match(
    mock_agreement_score_response: Mock,
    mock_parse_obj_as: Mock,
    mock_get_unique_scores: Mock,
    mock_task_metric: Mock,
    mock_agreement_score_comparing_result: Mock,
):
    min_match = 0.9
    mock_parse_obj_as.return_value = [MagicMock(spec=ResponseScore)]
    mock_task_metric.side_effect = (
        lambda task_from_id, task_to_id, metric_score: MagicMock(
            spec=TaskMetric,
            task_from_id=task_from_id,
            task_to_id=task_to_id,
            metric_score=metric_score,
        )
    )
    mock_agreement_score_comparing_result.return_value = MagicMock(
        spec=AgreementScoreComparingResult,
        agreement_score_reached=False,
        task_metrics=[mock_task_metric(1, 2, 0.95)],
    )
    result = compare_agreement_scores(mock_agreement_score_response, min_match)
    assert not result.agreement_score_reached


def test_compare_agreement_scores_empty_response(
    mock_parse_obj_as: Mock,
    mock_get_unique_scores: Mock,
    mock_task_metric: Mock,
    mock_agreement_score_comparing_result: Mock,
):
    min_match = 0.5
    mock_parse_obj_as.return_value = []
    mock_task_metric.return_value = MagicMock(spec=TaskMetric)
    mock_agreement_score_comparing_result.return_value = MagicMock(
        spec=AgreementScoreComparingResult,
        agreement_score_reached=False,
        task_metrics=[],
    )
    result = compare_agreement_scores([], min_match)
    assert not result.agreement_score_reached
    assert result.task_metrics == []


def test_save_agreement_metrics(mock_session: Mock):
    mock_scores = MagicMock()
    mock_scores.task_metrics = []
    save_agreement_metrics(mock_session, mock_scores)

    mock_session.bulk_save_objects.assert_called_once_with([])
    mock_session.commit.assert_called_once()


def test_get_annotation_tasks(mock_session: Mock):
    expected_tasks = [MagicMock(), MagicMock()]
    mock_query = mock_session.query.return_value.filter.return_value
    mock_query.all.return_value = expected_tasks

    result = get_annotation_tasks(
        mock_session, job_id=1, file_id=2, pages=[1, 2, 3]
    )

    mock_session.query.assert_called_once_with(ManualAnnotationTask)
    mock_session.query.return_value.filter.assert_called_once()
    mock_all = mock_session.query.return_value.filter.return_value.all
    mock_all.assert_called_once()
    assert result == expected_tasks


def test_get_accum_annotations():
    with patch("annotation.tasks.services.Session") as mock_session, patch(
        "annotation.tasks.services.accumulate_pages_info"
    ) as mock_accumulate_pages_info, patch(
        "annotation.tasks.services.construct_particular_rev_response"
    ) as mock_construct_particular_rev_response:

        annotation_task = MagicMock(ManualAnnotationTask)
        annotation_task.job_id = 1
        annotation_task.id = 2
        annotation_task.file_id = 3

        expected_revisions = [MagicMock(AnnotatedDoc)]
        mock_query = mock_session.query.return_value
        mock_query = mock_query.filter.return_value
        mock_query = mock_query.order_by.return_value
        mock_query.all.return_value = expected_revisions

        mock_accumulate_pages_info.return_value = (
            None,
            None,
            [1, 2, 3],
            None,
            None,
            MagicMock(),
        )
        mock_accumulate_pages_info.return_value[5].pages = [1, 2, 3]

        mock_construct_particular_rev_response.return_value = MagicMock(
            ParticularRevisionSchema
        )

        result = get_accum_annotations(
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

        annotation_task = MagicMock(ManualAnnotationTask)
        annotation_task.job_id = 1
        annotation_task.id = 2
        annotation_task.file_id = 3

        mock_query = mock_session.query.return_value
        mock_query = mock_query.filter.return_value
        mock_query = mock_query.order_by.return_value
        mock_query.all.return_value = []

        result = get_accum_annotations(
            db=mock_session,
            x_current_tenant="tenant_1",
            annotation_task=annotation_task,
        )

        mock_accumulate_pages_info.assert_not_called()
        mock_construct_particular_rev_response.assert_not_called()
        assert result is None


def test_get_accum_annotations_no_required_revision(mock_session: Mock):
    with patch(
        "annotation.tasks.services.accumulate_pages_info"
    ) as mock_accumulate_pages_info, patch(
        "annotation.tasks.services.construct_particular_rev_response"
    ) as mock_construct_particular_rev_response:

        annotation_task = MagicMock(ManualAnnotationTask)
        annotation_task.job_id = 1
        annotation_task.id = 2
        annotation_task.file_id = 3

        expected_revisions = [MagicMock(AnnotatedDoc)]
        mock_query = mock_session.query.return_value
        mock_query = mock_query.filter.return_value
        mock_query = mock_query.order_by.return_value
        mock_query.all.return_value = expected_revisions

        mock_accumulate_pages_info.return_value = (
            None,
            None,
            [1, 2, 3],
            None,
            None,
            None,
        )

        result = get_accum_annotations(
            db=mock_session,
            x_current_tenant="tenant_1",
            annotation_task=annotation_task,
        )

        mock_accumulate_pages_info.assert_called_once()
        mock_construct_particular_rev_response.assert_not_called()
        assert result is None


def test_remove_unnecessary_attributes():
    categories = {"category1", "category2"}

    page_annotations = MagicMock(spec=PageSchema)
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

    result = remove_unnecessary_attributes(categories, page_annotations)

    assert result == expected_result


@pytest.mark.parametrize(
    (
        "annotation_tasks",
        "get_accum_annotations_return_value",
        "expected_result",
    ),
    (
        (
            [MagicMock(spec=ManualAnnotationTask)],
            None,
            {},
        ),
        ([MagicMock(spec=ManualAnnotationTask)], MagicMock(pages=[]), {}),
        (
            [MagicMock(spec=ManualAnnotationTask)],
            MagicMock(
                pages=[
                    MagicMock(
                        page_num=1,
                        categories={"category1", "category2"},
                        pages=[MagicMock()],
                    )
                ]
            ),
            {1: {0: {"size": "A4", "objects": []}}},
        ),
    ),
)
def test_load_annotations(
    mock_session: Mock,
    annotation_tasks: List[Mock],
    get_accum_annotations_return_value: Mock,
    expected_result: Dict[int, Dict[int, Dict[str, Any]]],
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
        result = load_annotations(
            db=mock_session,
            x_current_tenant=mock_tenant,
            annotation_tasks=annotation_tasks,
        )

        assert result == expected_result
        mock_get_accum_annotations.assert_called_once_with(
            mock_session,
            mock_tenant,
            annotation_tasks[0] if annotation_tasks else None,
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
    id_mapping: Dict[Tuple[int], int],
    expected_result: Optional[int],
):
    result = get_new_id(old_id, id_mapping)
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
    old_id: int, id_mapping: Dict[Tuple[int], int], expected_result: Tuple[int]
):
    result = get_common_ids(old_id, id_mapping)
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

        result_links, result_children = get_links_and_children(
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
def test_get_common_values(items: List[List[Any]], expected: List[Any]):
    assert get_common_values(items) == expected


def test_change_ids():
    all_tasks_objs = {
        "task1": {"objects": [{"id": 1}, {"id": 2}]},
        "task2": {"objects": [{"id": 3}, {"id": 4}]},
    }

    doc_objs = {
        "doc1": {
            "objects": [
                {"id": 1, "links": [2], "children": [3]},
                {"id": 2},
                {"id": 3},
            ]
        }
    }

    id_mapping = {(1,): 101, (2,): 102, (3,): 103}

    mock_get_new_id = MagicMock(
        side_effect=lambda old_id, _: id_mapping.get((old_id,), old_id)
    )
    mock_get_common_ids = MagicMock(
        side_effect=lambda old_id, _: [id_mapping.get((old_id,), old_id)]
    )
    mock_get_links_and_children = MagicMock(
        side_effect=lambda ids, _, __: (
            [id_mapping.get((i,), i) for i in ids],
            [],
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

        change_ids(all_tasks_objs, doc_objs, id_mapping)

    assert doc_objs["doc1"]["objects"][0]["id"] == 101
    assert doc_objs["doc1"]["objects"][0]["links"] == [101]
    assert doc_objs["doc1"]["objects"][0]["children"] == [3]
    assert doc_objs["doc1"]["objects"][1]["id"] == 102
    assert doc_objs["doc1"]["objects"][2]["id"] == 103

    mock_get_new_id.assert_called()
    mock_get_common_ids.assert_called()
    mock_get_links_and_children.assert_called()
    mock_get_common_values.assert_called()


def test_change_ids_with_children():
    all_tasks_objs = {
        "task1": {"objects": [{"id": 1}, {"id": 2}, {"id": 3}]},
        "task2": {"objects": [{"id": 4}, {"id": 5}, {"id": 6}]},
    }

    doc_objs = {
        "doc1": {
            "objects": [
                {"id": 1, "links": [2], "children": [3, 4]},
                {"id": 2},
                {"id": 3},
            ]
        }
    }

    id_mapping = {(1,): 101, (2,): 102, (3,): 103, (4,): 104}

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

        change_ids(all_tasks_objs, doc_objs, id_mapping)

    assert doc_objs["doc1"]["objects"][0]["id"] == 101
    assert doc_objs["doc1"]["objects"][0]["links"] == [101]
    assert doc_objs["doc1"]["objects"][0]["children"] == [101]
    assert doc_objs["doc1"]["objects"][1]["id"] == 102
    assert doc_objs["doc1"]["objects"][2]["id"] == 103

    mock_get_new_id.assert_called()
    mock_get_common_ids.assert_called()
    mock_get_links_and_children.assert_called()
    mock_get_common_values.assert_called()


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

    result = remove_ids(task_obj)

    assert result == expected_result
    assert "id" not in result
    assert "links" not in result
    assert "children" not in result


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


def test_find_common_objs(setup_data: Dict[int, List[Tuple[Dict[str, str]]]]):
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

    result_common_objs, result_same_ids = find_common_objs(
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

    result_common_objs, result_same_ids = find_common_objs(
        task_data, all_tasks
    )

    assert result_common_objs == expected_common_objs
    assert result_same_ids == expected_same_ids


def test_find_common_objs_empty_data():
    task_data = {"objects": []}

    all_tasks = {}

    expected_common_objs = []
    expected_same_ids = {}

    result_common_objs, result_same_ids = find_common_objs(
        task_data, all_tasks
    )

    assert result_common_objs == expected_common_objs
    assert result_same_ids == expected_same_ids


@pytest.mark.parametrize(
    ("tasks", "expected"),
    (
        ({}, {}),
        (
            {
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
            },
            {
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
            },
        ),
        (
            {
                2: {
                    "objects": [
                        {
                            "id": "3",
                            "info": {"id": "b3", "value": "Nested Value"},
                        },
                    ]
                }
            },
            {2: [({"info": {"id": "b3", "value": "Nested Value"}}, "3")]},
        ),
        (
            {
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
            },
            {
                3: [({"name": "Task 4"}, "4"), ({"status": "Complete"}, "5")],
                4: [({"description": "Task 6"}, "6")],
            },
        ),
    ),
)
def test_get_tasks_without_ids(
    tasks: Dict[int, Any], expected: Dict[int, Any]
):
    assert get_tasks_without_ids(tasks) == expected


@pytest.fixture
def mock_dependencies():
    with patch(
        "annotation.tasks.services.get_file_path_and_bucket"
    ) as mock_get_file_path_and_bucket, patch(
        "annotation.tasks.services.get_annotation_tasks"
    ) as mock_get_annotation_tasks, patch(
        "annotation.tasks.services.construct_annotated_pages"
    ) as mock_construct_annotated_pages, patch(
        "annotation.tasks.services.construct_annotated_doc"
    ) as mock_construct_annotated_doc, patch(
        "annotation.tasks.services.update_task_status"
    ) as mock_update_task_status, patch(
        "annotation.tasks.services.Logger.exception"
    ) as mock_logger_exception:

        mock_get_file_path_and_bucket.return_value = ("s3/path", "bucket")
        mock_get_annotation_tasks.return_value = {}
        mock_construct_annotated_pages.return_value = ([], set())
        mock_construct_annotated_doc.return_value = None
        mock_update_task_status.return_value = None
        mock_logger_exception.return_value = None

        yield {
            "mock_get_file_path_and_bucket": mock_get_file_path_and_bucket,
            "mock_get_annotation_tasks": mock_get_annotation_tasks,
            "mock_construct_annotated_pages": mock_construct_annotated_pages,
            "mock_construct_annotated_doc": mock_construct_annotated_doc,
            "mock_update_task_status": mock_update_task_status,
            "mock_logger_exception": mock_logger_exception,
        }


def test_create_validation_revisions(mock_dependencies: Dict[str, Mock]):
    mock_db = MagicMock()
    x_current_tenant = "tenant_1"
    token = MagicMock(token="fake_token")
    job_id = 123
    validation_tasks = [
        ManualAnnotationTask(file_id=1, pages={1}, user_id=1, id=10)
    ]

    mock_dependencies["mock_construct_annotated_pages"].return_value = (
        [MagicMock(objs=True)],
        {"category1"},
    )
    mock_dependencies["mock_construct_annotated_doc"].return_value = None
    mock_dependencies["mock_update_task_status"].return_value = None

    with patch(
        "annotation.tasks.services.DocForSaveSchema"
    ) as mock_doc_for_save_schema:
        mock_doc_instance = mock_doc_for_save_schema.return_value
        mock_doc_instance.user = validation_tasks[0].user_id
        mock_doc_instance.pages = [MagicMock(objs=True)]
        mock_doc_instance.validated = set()
        mock_doc_instance.failed_validation_pages = set()
        mock_doc_instance.categories = {"category1"}

        create_validation_revisions(
            mock_db, x_current_tenant, token, job_id, validation_tasks
        )

        mock_dependencies[
            "mock_get_file_path_and_bucket"
        ].assert_called_once_with(1, x_current_tenant, token.token)
        mock_dependencies["mock_get_annotation_tasks"].assert_called_once_with(
            mock_db, job_id, 1, {1}
        )
        mock_dependencies[
            "mock_construct_annotated_pages"
        ].assert_called_once_with(mock_db, x_current_tenant, {})
        mock_dependencies[
            "mock_construct_annotated_doc"
        ].assert_called_once_with(
            db=mock_db,
            user_id=validation_tasks[0].user_id,
            pipeline_id=None,
            job_id=job_id,
            file_id=1,
            doc=mock_doc_instance,
            tenant=x_current_tenant,
            s3_file_path="s3/path",
            s3_file_bucket="bucket",
            latest_doc=None,
            task_id=validation_tasks[0].id,
            is_latest=True,
        )
        mock_dependencies["mock_update_task_status"].assert_called_once_with(
            mock_db, validation_tasks[0]
        )
        mock_dependencies["mock_logger_exception"].assert_not_called()


def test_create_validation_revisions_no_annotations(mock_dependencies: Mock):
    mock_db = MagicMock()
    x_current_tenant = "tenant_1"
    token = MagicMock(token="fake_token")
    job_id = 123
    validation_tasks = [
        ManualAnnotationTask(file_id=1, pages={1}, user_id=1, id=10)
    ]

    mock_dependencies["mock_get_annotation_tasks"].return_value = {}
    mock_dependencies["mock_construct_annotated_pages"].return_value = (
        [],
        set(),
    )

    create_validation_revisions(
        mock_db, x_current_tenant, token, job_id, validation_tasks
    )

    mock_dependencies["mock_get_file_path_and_bucket"].assert_called_with(
        1, x_current_tenant, token.token
    )
    mock_dependencies["mock_get_annotation_tasks"].assert_called_with(
        mock_db, job_id, 1, {1}
    )
    mock_dependencies["mock_construct_annotated_pages"].assert_called_with(
        mock_db, x_current_tenant, {}
    )
    mock_dependencies["mock_construct_annotated_doc"].assert_not_called()
    mock_dependencies["mock_update_task_status"].assert_not_called()
    mock_dependencies["mock_logger_exception"].assert_not_called()


def test_create_validation_revisions_construct_doc_value_error(
    mock_dependencies: Mock,
):
    mock_db = MagicMock()
    x_current_tenant = "tenant_1"
    token = MagicMock(token="fake_token")
    job_id = 123
    validation_tasks = [
        ManualAnnotationTask(file_id=1, pages={1}, user_id=1, id=10)
    ]

    mock_dependencies["mock_construct_annotated_pages"].return_value = (
        [MagicMock(objs=True)],
        {"category1"},
    )
    mock_dependencies["mock_construct_annotated_doc"].side_effect = ValueError(
        "Test error"
    )

    with patch(
        "annotation.tasks.services.DocForSaveSchema"
    ) as mock_doc_for_save_schema:
        mock_doc_instance = mock_doc_for_save_schema.return_value
        mock_doc_instance.user = validation_tasks[0].user_id
        mock_doc_instance.pages = [MagicMock(objs=True)]
        mock_doc_instance.validated = set()
        mock_doc_instance.failed_validation_pages = set()
        mock_doc_instance.categories = {"category1"}

        create_validation_revisions(
            mock_db, x_current_tenant, token, job_id, validation_tasks
        )

        mock_dependencies[
            "mock_get_file_path_and_bucket"
        ].assert_called_once_with(1, x_current_tenant, token.token)
        mock_dependencies["mock_get_annotation_tasks"].assert_called_once_with(
            mock_db, job_id, 1, {1}
        )
        mock_dependencies[
            "mock_construct_annotated_pages"
        ].assert_called_once_with(mock_db, x_current_tenant, {})
        mock_dependencies[
            "mock_construct_annotated_doc"
        ].assert_called_once_with(
            db=mock_db,
            user_id=validation_tasks[0].user_id,
            pipeline_id=None,
            job_id=job_id,
            file_id=1,
            doc=mock_doc_instance,
            tenant=x_current_tenant,
            s3_file_path="s3/path",
            s3_file_bucket="bucket",
            latest_doc=None,
            task_id=validation_tasks[0].id,
            is_latest=True,
        )
        mock_dependencies["mock_logger_exception"].assert_called_once_with(
            "Cannot save first validation revision."
        )
        mock_dependencies["mock_update_task_status"].assert_not_called()


def test_construct_annotated_pages(mock_session: Mock):
    x_current_tenant = "tenant_1"

    with patch(
        "annotation.tasks.services.PageSchema", return_value=MagicMock()
    ):
        pages, categories = construct_annotated_pages(
            mock_session, x_current_tenant, []
        )
        assert pages == []
        assert categories == set()


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
    ), patch("annotation.tasks.services.PageSchema", return_value=MagicMock()):
        _, categories = construct_annotated_pages(
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
    ), patch("annotation.tasks.services.PageSchema", return_value=MagicMock()):
        _, categories = construct_annotated_pages(
            mock_session, x_current_tenant, annotation_tasks
        )
        assert categories == expected_categories
