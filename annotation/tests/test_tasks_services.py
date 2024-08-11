from unittest.mock import Mock, call, patch

from annotation.models import File
import pytest
from sqlalchemy.orm import Session

from annotation.errors import FieldConstraintError
from annotation.jobs.services import ValidationSchema
from annotation.tasks.services import validate_files_info, validate_task_info, validate_users_info


TEST_PARAMS_INVALID_FILES = [
    (
        {
            "file_id": 1,
            "job_id": 2,
            "pages": [1, 2, 4],
        },
        Mock(spec=File, pages_number=3),
        "pages ({4}) do not belong to file"
    ),
    (
        {
            "file_id": 1,
            "job_id": 2,
            "pages": [1, 2, 3],
        },
        None,
        "file with id 1 is not assigned for job 2"
    ),
]


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
    db_session: Session, task_info: dict, validation_type: ValidationSchema, is_validation: bool
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
        mock_validate_files_info.assert_called_once_with(
            db_session, task_info
        )


@pytest.mark.parametrize(
    ("validation_type", "is_validation"),
    (
        (ValidationSchema.validation_only, False),
    ),
)
def test_validate_task_info_negative_case(
    db_session: Session,task_info: dict, validation_type: ValidationSchema, is_validation: bool
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
    )
)
def test_validate_users_info_positive_case(
    db_session: Session, task_info: dict, validation_type: ValidationSchema, is_validation: bool, mock_function: str, mock_return_value: bool
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
        (False,"user 1 is not assigned as annotator for job 2")
    )
)
def test_validate_users_info_negative_case(db_session: Session, task_info: dict, is_validation: bool, expected_error_message: str):
    task_info["is_validation"] = is_validation
    db_session.query().filter_by().first.return_value = None
    with pytest.raises(FieldConstraintError) as excinfo:
        validate_users_info(db_session, task_info, ValidationSchema.validation_only)
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
    db_session.query.assert_has_calls([
        call(File),
    ])
    mock_query.filter_by.assert_called_once_with(file_id=1, job_id=2)
    

@pytest.mark.parametrize(
    ("task_info", "mock_file", "expected_error_message"),
    TEST_PARAMS_INVALID_FILES
)
def test_validate_files_info_negative_case(db_session: Session, task_info: dict, mock_file: Mock, expected_error_message: str):
    db_session.query().filter_by().first.return_value = mock_file

    with pytest.raises(FieldConstraintError) as excinfo:
        validate_files_info(db_session, task_info)
    
    assert expected_error_message in str(excinfo.value)