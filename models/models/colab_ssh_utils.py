import logging
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator, Union

from botocore.response import StreamingBody
from paramiko import AutoAddPolicy, SSHClient
from paramiko.ssh_exception import SSHException

from models.constants import MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY
from models.errors import ColabFileUploadError
from models.schemas import TrainingCredentials
from models.utils import get_host

LOGGER = logging.getLogger(name="models")
COLAB_TRAINING_DIRECTORY = "/content/training/"
COLAB_TRAINING_RESULTS_DIRECTORY = COLAB_TRAINING_DIRECTORY + "results/"


@contextmanager
def connect_colab(credentials: TrainingCredentials) -> Iterator[SSHClient]:
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    LOGGER.info("Connecting to colab...")
    try:
        client.connect(
            hostname=credentials.host,
            port=credentials.port,
            username=credentials.user,
            password=credentials.password,
        )
        yield client
    except SSHException:
        LOGGER.info("Connection failed")
        raise
    finally:
        client.close()


def upload_file_to_colab(
    ssh_client: SSHClient,
    file_obj: Union[BinaryIO, StreamingBody],
    file_size: int,
    file_name: str,
) -> None:
    file_path = COLAB_TRAINING_DIRECTORY + file_name
    ssh_client.exec_command(f"mkdir -p {COLAB_TRAINING_DIRECTORY}")
    with ssh_client.open_sftp() as sftp_session:
        response = sftp_session.putfo(file_obj, str(file_path), confirm=True)
    if response.st_size != file_size:
        LOGGER.info("File upload error")
        raise ColabFileUploadError(
            f"File {file_name} was corrupted during upload into colab"
        )
    LOGGER.info("File was successfully uploaded")


def check_aws_credentials_file(home_directory: Path) -> None:
    aws_creds_file = home_directory / ".aws" / "credentials"
    if aws_creds_file.is_file():
        LOGGER.info("Using existing aws credentials file")
    else:
        LOGGER.info("Creating aws credentials file")
        aws_creds_file.parent.mkdir(parents=True, exist_ok=True)
        with aws_creds_file.open("w") as cred_file:
            cred_file.writelines(
                (
                    "[default]\n",
                    f"aws_access_key_id={MINIO_ACCESS_KEY}\n",
                    f"aws_secret_access_key={MINIO_SECRET_KEY}\n",
                ),
            )


def local_mount_colab_drive(
    temp_directory: str, credentials: TrainingCredentials
) -> None:
    mount_command = (
        f"sshfs -o StrictHostKeyChecking=no,password_stdin,nonempty "
        f"-p {credentials.port} {credentials.user}@{credentials.host}:"
        f"{COLAB_TRAINING_RESULTS_DIRECTORY} {temp_directory}"
    )
    try:
        subprocess.run(
            mount_command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            input=credentials.password,
        )
    except subprocess.SubprocessError as error:
        LOGGER.info(f"Subprocess execution error: {error}")
        raise
    LOGGER.info(
        f"Remote directory {COLAB_TRAINING_RESULTS_DIRECTORY} "
        f"successfully mounted at local {temp_directory} path."
    )


def sync_colab_with_minio(
    temp_directory: str, tenant: str, training_id: int
) -> None:
    syn_command = (
        f"aws --endpoint-url http://{get_host(MINIO_HOST)} "
        f"s3 sync {temp_directory} "
        f"s3://{tenant}/trainings/{training_id}/results/ --delete"
    )
    try:
        subprocess.run(
            syn_command, shell=True, capture_output=True, text=True, check=True
        )
    except subprocess.SubprocessError as error:
        LOGGER.info(f"Subprocess execution error: {error}")
        raise
    finally:
        subprocess.run(f"fusermount -u {temp_directory}", shell=True)
        LOGGER.info("Remote directory successfully unmounted.")
    LOGGER.info(f"All remote results uploaded to minio bucket: {tenant}")
