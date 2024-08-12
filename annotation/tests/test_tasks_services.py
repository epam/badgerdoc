import re
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
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session, patch(
        "annotation.tasks.services.validate_users_info"
    ) as mock_validate_users_info, patch(
        "annotation.tasks.services.validate_files_info"
    ) as mock_validate_files_info:

        db_session = mock_session()
        task_info = {"is_validation": is_validation}

        validate_task_info(db_session, task_info, validation_type)

        mock_validate_users_info.assert_called_once_with(
            db_session, task_info, validation_type
        )
        mock_validate_files_info.assert_called_once_with(db_session, task_info)


def test_validate_task_info_invalid_task_info():
    with patch("sqlalchemy.orm.Session", spec=True) as mock_session:
        db_session = mock_session()
        task_info = {"is_validation": False}
        validation_type = ValidationSchema.validation_only

        with pytest.raises(FieldConstraintError):
            validate_task_info(db_session, task_info, validation_type)


@pytest.mark.parametrize(
    ("is_validation"),
    (
        (True),
        (False),
    ),
)
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
    (
        (True, "validator"),
        (False, "annotator"),
    ),
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
        "not_processed",
        "annotation_user",
        "validation_user",
        "expected_error_message_pattern",
    ),
    (
        (
            {1},
            set(),
            set(),
            False,
            True,
            r"Missing `annotation_user_for_failed_pages` param",
        ),
        (
            set(),
            {2},
            set(),
            True,
            False,
            r"Missing `validation_user_for_reannotated_pages` param",
        ),
    ),
)
def test_validate_user_actions_missing_users(
    failed: set,
    annotated: set,
    not_processed: set,
    annotation_user: bool,
    validation_user: bool,
    expected_error_message_pattern: str,
):
    with pytest.raises(HTTPException) as excinfo:
        validate_user_actions(
            is_validation=True,
            failed=failed,
            annotated=annotated,
            not_processed=not_processed,
            annotation_user=annotation_user,
            validation_user=validation_user,
        )
    assert re.match(expected_error_message_pattern, excinfo.value.detail)


@pytest.mark.parametrize(
    (
        "failed",
        "annotated",
        "not_processed",
        "annotation_user",
        "validation_user",
        "expected_error_message_pattern",
    ),
    (
        (
            set(),
            set(),
            set(),
            True,
            True,
            r"Validator did not mark any pages as failed",
        ),
        (
            {1},
            set(),
            set(),
            True,
            True,
            r"Validator did not edit any pages",
        ),
        (
            {1},
            {2},
            {3},
            True,
            True,
            r"Cannot finish validation task. There are not processed pages",
        ),
    ),
)
def test_validate_user_actions_invalid_states(
    failed: set,
    annotated: set,
    not_processed: set,
    annotation_user: bool,
    validation_user: bool,
    expected_error_message_pattern: str,
):
    with pytest.raises(HTTPException) as excinfo:
        validate_user_actions(
            is_validation=True,
            failed=failed,
            annotated=annotated,
            not_processed=not_processed,
            annotation_user=annotation_user,
            validation_user=validation_user,
        )
    assert re.match(expected_error_message_pattern, excinfo.value.detail)
