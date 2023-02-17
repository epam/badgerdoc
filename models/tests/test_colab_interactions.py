from io import StringIO
from unittest import mock

import pytest

from models.colab_ssh_utils import (
    COLAB_TRAINING_DIRECTORY,
    connect_colab,
    upload_file_to_colab,
)
from models.errors import ColabFileUploadError

TEST_FILE_NAME = "test_file.py"
TEST_CREDENTIALS = {
    "hostname": "test_host",
    "port": 12345,
    "username": "test_user",
    "password": "test_password",
}


class MockCredentialsSchema:
    host = TEST_CREDENTIALS["hostname"]
    port = TEST_CREDENTIALS["port"]
    user = TEST_CREDENTIALS["username"]
    password = TEST_CREDENTIALS["password"]


class MockSFTPContext:
    mock_sftp_session = mock.Mock()
    file_object_stat_mock = mock.Mock()
    file_object_stat_mock.st_size = 1
    mock_sftp_session.putfo = mock.Mock(return_value=file_object_stat_mock)

    def __enter__(self):
        return self.__class__.mock_sftp_session

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_connect_colab_called_with_credentials(monkeypatch) -> None:
    """Tests that paramiko SSHClient().connect will be called with
    provided credentials.
    """
    mock_client = mock.Mock()
    mock_ssh = mock.Mock(return_value=mock_client)
    mock_policy = mock.Mock()
    monkeypatch.setattr(
        "models.colab_ssh_utils.SSHClient",
        mock_ssh,
    )
    monkeypatch.setattr(
        "models.colab_ssh_utils.AutoAddPolicy",
        mock.Mock(return_value=mock_policy),
    )
    mock_client.connect = mock.Mock(return_value=1)
    mock_client.set_missing_host_key_policy = mock.Mock(return_value=1)
    with connect_colab(MockCredentialsSchema):
        mock_ssh.assert_called()
        mock_client.connect.assert_called_with(**TEST_CREDENTIALS)
        mock_client.set_missing_host_key_policy.assert_called_with(mock_policy)


def test_upload_file_to_colab(monkeypatch) -> None:
    """Tests that 'mkdir -p' with COLAB_TRAINING_DIRECTORY + file_name
    was called in 'ssh_client.exec_command' and 'ssh_client.open_sftp().putfo'
    method was called with correct arguments if file wasn't corrupted.
    """
    test_command = f"mkdir -p {COLAB_TRAINING_DIRECTORY}"
    test_file = StringIO("test")
    ssh_client = mock.Mock()
    ssh_client.exec_command = mock.Mock()
    ssh_client.open_sftp = MockSFTPContext
    upload_file_to_colab(ssh_client, test_file, 1, TEST_FILE_NAME)
    ssh_client.exec_command.assert_called_with(test_command)
    ssh_client.open_sftp.mock_sftp_session.putfo.assert_called_with(
        test_file, f"{COLAB_TRAINING_DIRECTORY}{TEST_FILE_NAME}", confirm=True
    )


def test_connect_upload_file_to_colab_upload_error() -> None:
    """Tests that if size of uploaded object not equal to provided
    file object's size - ColabFileUploadError will be raised with
    'File was corrupted during upload into colab' message.
    """
    test_file = StringIO("test")
    ssh_client = mock.Mock()
    ssh_client.exec_command = mock.Mock()
    ssh_client.open_sftp = MockSFTPContext
    with pytest.raises(
        ColabFileUploadError,
        match=f"File {TEST_FILE_NAME} was corrupted during upload",
    ):
        upload_file_to_colab(ssh_client, test_file, 2, TEST_FILE_NAME)
