from unittest.mock import Mock

import pytest
from botocore.exceptions import BotoCoreError
from paramiko.ssh_exception import SSHException
from sqlalchemy.exc import SQLAlchemyError

from .override_app_dependency import (OTHER_TENANT_HEADER, TEST_HEADER,
                                      TEST_TENANTS)

TEST_CREDENTIALS = {
    "host": "test_host",
    "port": 12345,
    "user": "test_user",
    "password": "test_password",
}
START_TRAINING_PATH = "/trainings/{0}/start"
EXIST_TRAINING_ID = 1
NOT_EXIST_TRAINING_ID = 2
BASEMENT_ID = "base_id"
TRAINING_SCRIPT_KEY = f"basements/{BASEMENT_ID}/training_script.py"
TRAINING_ARCHIVE_NAME = "training_archive.zip"
TRAINING_ARCHIVE_KEY = f"basements/{BASEMENT_ID}/{TRAINING_ARCHIVE_NAME}"
TRAINING_SCRIPT_DATA = "script"
TRAINING_ARCHIVE_DATA = "archive"


@pytest.mark.integration
def test_start_training_db_error(monkeypatch, overrided_token_client) -> None:
    """Test handling of db connection errors"""
    monkeypatch.setattr(
        "models.crud.Session.query",
        Mock(side_effect=SQLAlchemyError("some error message")),
    )
    response = overrided_token_client.post(
        START_TRAINING_PATH.format(EXIST_TRAINING_ID),
        json=TEST_CREDENTIALS,
        headers=TEST_HEADER,
    )
    assert response.status_code == 500
    assert "Error: connection error (some error message)" in response.text


@pytest.mark.integration
@pytest.mark.parametrize("prepare_db_start_training", [None], indirect=True)
def test_start_training_not_existing_training_error(
    monkeypatch, overrided_token_client, prepare_db_start_training
) -> None:
    """Tests that not existing training_id provided will return 404 status
    with 'Not existing training' message.
    """
    response = overrided_token_client.post(
        START_TRAINING_PATH.format(NOT_EXIST_TRAINING_ID),
        json=TEST_CREDENTIALS,
        headers=TEST_HEADER,
    )
    assert response.status_code == 404
    assert "Not existing training" in response.text


@pytest.mark.integration
@pytest.mark.parametrize("prepare_db_start_training", [None], indirect=True)
def test_start_training_no_key_script_error(
    client, prepare_db_start_training, overrided_token_client
):
    """Tests that if training has no key_script saved in DB resource will
    return 400 status with 'Training has no training script yet' message.
    """
    response = overrided_token_client.post(
        START_TRAINING_PATH.format(EXIST_TRAINING_ID),
        json=TEST_CREDENTIALS,
        headers=TEST_HEADER,
    )
    assert response.status_code == 400
    assert f"{EXIST_TRAINING_ID} has no training script yet" in response.text


@pytest.mark.integration
@pytest.mark.skip(
    "Test should be fixed - got 'Annotation dataset for training 1 not ready' in response"
)
@pytest.mark.parametrize(
    "prepare_db_start_training", [TRAINING_ARCHIVE_KEY], indirect=True
)
def test_start_training_colab_connection_error(
    monkeypatch, prepare_db_start_training, overrided_token_client
) -> None:
    """Tests that ssh connection errors will raise 500 status with error
    description in message.
    """
    monkeypatch.setattr(
        "models.routers.training_routers.connect_colab",
        Mock(side_effect=SSHException("some ssh error")),
    )
    response = overrided_token_client.post(
        START_TRAINING_PATH.format(EXIST_TRAINING_ID),
        json=TEST_CREDENTIALS,
        headers=TEST_HEADER,
    )
    assert response.status_code == 500
    assert "Error: ssh connection error (some ssh error)" in response.text


class MockSSHContext:
    def __init__(self, *args):
        pass

    def __enter__(self):
        return Mock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.integration
@pytest.mark.skip(
    "Test should be fixed - got 'Annotation dataset for training 1 not ready' in response"
)
@pytest.mark.parametrize(
    "prepare_db_start_training", [TRAINING_ARCHIVE_KEY], indirect=True
)
def test_start_training_no_such_bucket_error(
    monkeypatch,
    prepare_db_start_training,
    moto_minio,
    overrided_token_client,
) -> None:
    """Tests that x-current-tenant with not existing bucket provided will
    return 404 status with 'Bucket for tenant does not exist' message.
    """
    other_tenant = TEST_TENANTS[1]
    monkeypatch.setattr(
        "models.utils.boto3.resource",
        Mock(return_value=moto_minio),
    )
    monkeypatch.setattr(
        "models.routers.training_routers.connect_colab", MockSSHContext
    )
    response = overrided_token_client.post(
        START_TRAINING_PATH.format(EXIST_TRAINING_ID),
        json=TEST_CREDENTIALS,
        headers=OTHER_TENANT_HEADER,
    )
    assert response.status_code == 404
    assert f"Bucket for tenant {other_tenant} does not exist" in response.text


@pytest.mark.integration
@pytest.mark.skip(
    "Test should be fixed - got 'Annotation dataset for training 1 not ready' in response"
)
@pytest.mark.parametrize(
    "prepare_db_start_training",
    [TRAINING_ARCHIVE_KEY],
    indirect=True,
)
def test_start_training_boto3_error(
    monkeypatch, prepare_db_start_training, overrided_token_client
) -> None:
    """Tests that boto3 errors while connecting minio will
    return 500 status with error description in message.
    """
    monkeypatch.setattr(
        "models.routers.training_routers.get_minio_object",
        Mock(side_effect=BotoCoreError()),
    )
    monkeypatch.setattr(
        "models.routers.training_routers.connect_colab", MockSSHContext
    )
    response = overrided_token_client.post(
        START_TRAINING_PATH.format(EXIST_TRAINING_ID),
        json=TEST_CREDENTIALS,
        headers=TEST_HEADER,
    )
    assert response.status_code == 500
    assert "Error: connection error " in response.text


@pytest.mark.integration
@pytest.mark.skip(
    "Test should be fixed - got 'Annotation dataset for training 1 not ready' in response"
)
@pytest.mark.parametrize(
    "prepare_db_start_training",
    [TRAINING_ARCHIVE_KEY],
    indirect=True,
)
def test_start_training_integration(
    monkeypatch,
    prepare_db_start_training,
    save_start_training_minio_objects,
    overrided_token_client,
) -> None:
    """Tests that with correct arguments and no errors function will return
    200 status code with 'Training with id {training_id} is started' message.
    """
    mock_upload = Mock()
    monkeypatch.setattr(
        "models.routers.training_routers.upload_file_to_colab", mock_upload
    )
    monkeypatch.setattr(
        "models.utils.boto3.resource",
        Mock(return_value=save_start_training_minio_objects),
    )
    monkeypatch.setattr(
        "models.routers.training_routers.connect_colab", MockSSHContext
    )
    response = overrided_token_client.post(
        START_TRAINING_PATH.format(EXIST_TRAINING_ID),
        json=TEST_CREDENTIALS,
        headers=TEST_HEADER,
    )
    assert mock_upload.call_count == 2
    ssh_client, file_object, file_size, file_name = mock_upload.call_args.args
    assert file_object.read().decode("utf-8") == TRAINING_ARCHIVE_DATA
    assert file_size == len(TRAINING_ARCHIVE_DATA)
    assert file_name == TRAINING_ARCHIVE_NAME
    assert response.status_code == 200
    assert f"Training with id {EXIST_TRAINING_ID} is started" in response.text
