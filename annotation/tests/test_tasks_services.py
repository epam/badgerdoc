from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from annotation.errors import FieldConstraintError
from annotation.jobs.services import ValidationSchema
from annotation.tasks.services import validate_task_info


@pytest.fixture
def db_session():
    """Fixture for creating a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def task_info():
    """Fixture for creating a mock task_info dictionary."""
    return {"is_validation": True}


@pytest.mark.parametrize(
    "validation_type, is_validation, should_raise_error",
    [
        (ValidationSchema.validation_only, False, True),
        (ValidationSchema.validation_only, True, False),
        ("other_type", False, False),
        ("other_type", True, False),
    ],
)
def test_validate_task_info(
    db_session, task_info, validation_type, is_validation, should_raise_error
):
    task_info["is_validation"] = is_validation

    if should_raise_error:
        with pytest.raises(FieldConstraintError):
            validate_task_info(db_session, task_info, validation_type)
    else:
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
