from typing import Dict, List, Union
from unittest.mock import Mock, call, patch

import pytest
from fastapi import HTTPException

from annotation.errors import FieldConstraintError
from annotation.jobs.services import ValidationSchema
from annotation.models import File, ManualAnnotationTask
from annotation.tasks.services import (
    check_cross_annotating_pages,
    validate_files_info,
    validate_task_info,
    validate_user_actions,
    validate_users_info,
)


@patch("sqlalchemy.orm.Session", spec=True)
@pytest.mark.parametrize(
    ("validation_type", "is_validation"),
    (
        (ValidationSchema.validation_only, True),
        ("other_type", False),
        ("other_type", True),
    ),
)
def test_validate_task_info(
    mock_session: Mock,
    validation_type: ValidationSchema,
    is_validation: bool,
):
    db_session = mock_session()
    task_info = {"is_validation": is_validation}

    with patch(
        "annotation.tasks.services.validate_users_info"
    ) as mock_validate_users_info, patch(
        "annotation.tasks.services.validate_files_info"
    ) as mock_validate_files_info:
        validate_task_info(db_session, task_info, validation_type)
        mock_validate_users_info.assert_called_once_with(
            db_session, task_info, validation_type
        )
        mock_validate_files_info.assert_called_once_with(db_session, task_info)


@patch("sqlalchemy.orm.Session", spec=True)
def test_validate_task_info_raises_error_for_invalid_task_info(
    mock_session: Mock,
):
    db_session = mock_session()
    task_info = {"is_validation": False}
    validation_type = ValidationSchema.validation_only

    with pytest.raises(FieldConstraintError):
        validate_task_info(db_session, task_info, validation_type)


@patch("sqlalchemy.orm.Session", spec=True)
@pytest.mark.parametrize(
    ("validation_type", "is_validation"),
    (
        (ValidationSchema.validation_only, True),
        (ValidationSchema.validation_only, False),
    ),
)
def test_validate_users_info(
    mock_session: Mock, validation_type: ValidationSchema, is_validation: bool
):
    db_session = mock_session()
    task_info = {
        "is_validation": is_validation,
        "user_id": 1,
        "job_id": 2,
    }

    validation_type = ValidationSchema.validation_only
    db_session.query().filter_by().first().return_value = True

    validate_users_info(db_session, task_info, validation_type)

    assert db_session.query.call_count == 2


@patch("sqlalchemy.orm.Session", spec=True)
def test_validate_users_info_calls_check_cross_annotating_pages(
    mock_session: Mock,
):
    db_session = mock_session()
    task_info = {
        "is_validation": True,
        "user_id": 1,
        "job_id": 2,
    }

    with patch(
        f"annotation.tasks.services.{'check_cross_annotating_pages'}"
    ) as mock_func:
        validate_users_info(db_session, task_info, ValidationSchema.cross)
        mock_func.assert_called_once_with(db_session, task_info)


@patch("sqlalchemy.orm.Session", spec=True)
@pytest.mark.parametrize(
    ("is_validation", "validator_or_annotator"),
    [
        (True, "validator"),
        (False, "annotator"),
    ],
)
def test_validate_users_info_raises_error_for_invalid_users_info(
    mock_session: Mock,
    is_validation: bool,
    validator_or_annotator: str,
):
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


@patch("sqlalchemy.orm.Session", spec=True)
def test_validate_files_info(mock_session: Mock):
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


@patch("sqlalchemy.orm.Session", spec=True)
@pytest.mark.parametrize(
    ("task_info", "mock_file", "expected_error_message_regex"),
    (
        (
            {
                "file_id": 1,
                "job_id": 2,
                "pages": [1, 2, 4],
            },
            Mock(spec=File, pages_number=3),
            r"pages \(\{4\}\) do not belong to file",
        ),
        (
            {
                "file_id": 1,
                "job_id": 2,
                "pages": [1, 2, 3],
            },
            None,
            r"file with id 1 is not assigned for job 2",
        ),
    ),
)
def test_validate_files_info_raises_error_for_invalid_file_info(
    mock_session: Mock,
    task_info: Dict[str, Union[int, List[int]]],
    mock_file: Mock,
    expected_error_message_regex: str,
):
    db_session = mock_session()
    db_session.query().filter_by().first.return_value = mock_file

    with pytest.raises(
        FieldConstraintError, match=expected_error_message_regex
    ):
        validate_files_info(db_session, task_info)


@patch("sqlalchemy.orm.Session", spec=True)
def test_check_cross_annotating_pages(mock_session: Mock):
    db_session = mock_session()
    task_info = {"user_id": 1, "file_id": 2, "job_id": 3, "pages": {4, 5}}
    existing_pages = []

    mock_query = db_session.query.return_value
    mock_query.filter.return_value.all.return_value = [(existing_pages,)]

    try:
        check_cross_annotating_pages(db_session, task_info)

        assert db_session.query.call_count == 1
        db_session.query.assert_has_calls(
            [
                call(ManualAnnotationTask.pages),
            ]
        )
        mock_query.filter.assert_called_once()

    except FieldConstraintError:
        pytest.fail("FieldConstraintError was raised unexpectedly")


@patch("sqlalchemy.orm.Session", spec=True)
def test_check_cross_annotating_pages_raise_error_when_page_already_annotated(
    mock_session: Mock,
):
    db_session = mock_session()
    task_info = {"user_id": 1, "file_id": 2, "job_id": 3, "pages": {4, 5}}
    existing_pages = [4, 5]

    mock_query = db_session.query.return_value
    mock_query.filter.return_value.all.return_value = [(existing_pages,)]

    expected_error_message = (
        "within cross validation job user can't validate file's pages "
        "that are already distributed in annotation tasks for this user: "
        "{4, 5}"
    )

    with pytest.raises(FieldConstraintError, match=expected_error_message):
        check_cross_annotating_pages(db_session, task_info)


@pytest.mark.parametrize(
    (
        "is_validation",
        "failed",
        "annotated",
        "not_processed",
        "annotation_user",
        "validation_user",
        "expected_error_message",
    ),
    (
        (
            True,
            {1},
            set(),
            set(),
            False,
            True,
            "Missing `annotation_user_for_failed_pages` param "
            "for failed pages.",
        ),
        (
            True,
            set(),
            {2},
            set(),
            True,
            False,
            "Missing `validation_user_for_reannotated_pages` param "
            "for edited pages.",
        ),
        (
            True,
            set(),
            set(),
            set(),
            True,
            True,
            "Validator did not mark any pages as failed, thus "
            "`annotation_user_for_failed_pages` param should be null.",
        ),
        (
            True,
            {1},
            set(),
            set(),
            True,
            True,
            "Validator did not edit any pages, thus "
            "`validation_user_for_reannotated_pages` param should be null.",
        ),
        (
            True,
            {1},
            {2},
            {3},
            True,
            True,
            "Cannot finish validation task. There are not processed pages: "
            "{3}",
        ),
    ),
)
def test_validate_user_actions_raises_error_for_invalid_user_states(
    is_validation: bool,
    failed: set,
    annotated: set,
    not_processed: set,
    annotation_user: bool,
    validation_user: bool,
    expected_error_message: str,
):
    with pytest.raises(HTTPException) as excinfo:
        validate_user_actions(
            is_validation=is_validation,
            failed=failed,
            annotated=annotated,
            not_processed=not_processed,
            annotation_user=annotation_user,
            validation_user=validation_user,
        )
    assert excinfo.value.detail == expected_error_message
