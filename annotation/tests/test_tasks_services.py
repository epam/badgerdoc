from unittest.mock import Mock, call, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

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

TEST_PARAMS_INVALID_FILES = (
    (
        {
            "file_id": 1,
            "job_id": 2,
            "pages": [1, 2, 4],
        },
        Mock(spec=File, pages_number=3),
        "pages ({4}) do not belong to file",
    ),
    (
        {
            "file_id": 1,
            "job_id": 2,
            "pages": [1, 2, 3],
        },
        None,
        "file with id 1 is not assigned for job 2",
    ),
)


TEST_PARAMS_VALIDATE_USER_ACTIONS = (
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
        "Cannot finish validation task. There are not processed pages: " "{3}",
    ),
)


@pytest.fixture(scope="function")
def db_session():
    return Mock(spec=Session)


@pytest.fixture(scope="function")
def task_info():
    return {
        "is_validation": True,
        "user_id": 1,
        "job_id": 2,
    }


@pytest.mark.parametrize(
    ("validation_type", "is_validation"),
    (
        (ValidationSchema.validation_only, True),
        ("other_type", False),
        ("other_type", True),
    ),
)
def test_validate_task_info_positive_case(
    db_session: Session,
    task_info: dict,
    validation_type: ValidationSchema,
    is_validation: bool,
):
    task_info["is_validation"] = is_validation

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


@pytest.mark.parametrize(
    ("validation_type", "is_validation"),
    ((ValidationSchema.validation_only, False),),
)
def test_validate_task_info_negative_case(
    db_session: Session,
    task_info: dict,
    validation_type: ValidationSchema,
    is_validation: bool,
):
    task_info["is_validation"] = is_validation

    with pytest.raises(FieldConstraintError):
        validate_task_info(db_session, task_info, validation_type)


@pytest.mark.parametrize(
    "validation_type, is_validation, mock_function, mock_return_value",
    (
        (ValidationSchema.cross, True, "check_cross_annotating_pages", True),
        (ValidationSchema.validation_only, True, None, True),
        (ValidationSchema.validation_only, False, None, True),
    ),
)
def test_validate_users_info_positive_case(
    db_session: Session,
    task_info: dict,
    validation_type: ValidationSchema,
    is_validation: bool,
    mock_function: str,
    mock_return_value: bool,
):
    task_info["is_validation"] = is_validation

    if mock_function:
        with patch(f"annotation.tasks.services.{mock_function}") as mock_func:
            validate_users_info(db_session, task_info, validation_type)
            mock_func.assert_called_once_with(db_session, task_info)
    else:
        db_session.query().filter_by().first.return_value = mock_return_value
        validate_users_info(db_session, task_info, validation_type)


@pytest.mark.parametrize(
    ("is_validation", "expected_error_message"),
    (
        (True, "user 1 is not assigned as validator for job 2"),
        (False, "user 1 is not assigned as annotator for job 2"),
    ),
)
def test_validate_users_info_negative_case(
    db_session: Session,
    task_info: dict,
    is_validation: bool,
    expected_error_message: str,
):
    task_info["is_validation"] = is_validation
    db_session.query().filter_by().first.return_value = None
    with pytest.raises(FieldConstraintError) as excinfo:
        validate_users_info(
            db_session, task_info, ValidationSchema.validation_only
        )
    assert expected_error_message in str(excinfo.value)


def test_validate_files_info_positive_case(db_session: Session):
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
    db_session.query.assert_has_calls(
        [
            call(File),
        ]
    )
    mock_query.filter_by.assert_called_once_with(file_id=1, job_id=2)


@pytest.mark.parametrize(
    ("task_info", "mock_file", "expected_error_message"),
    TEST_PARAMS_INVALID_FILES,
)
def test_validate_files_info_negative_case(
    db_session: Session,
    task_info: dict,
    mock_file: Mock,
    expected_error_message: str,
):
    db_session.query().filter_by().first.return_value = mock_file

    with pytest.raises(FieldConstraintError) as excinfo:
        validate_files_info(db_session, task_info)

    assert expected_error_message in str(excinfo.value)


def test_check_cross_annotating_pages_positive_case(db_session: Session):
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


def test_check_cross_annotating_pages_negative_case(db_session: Session):
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
    TEST_PARAMS_VALIDATE_USER_ACTIONS,
)
def test_validate_user_actions_negative_case(
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
