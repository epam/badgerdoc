import os.path
from pathlib import Path
from typing import Any, Callable, List, Optional

from minio import Minio, error
from mypy_extensions import VarArg

from . import logger  # type: ignore

LOGGER = logger.get_logger(
    __name__, "MINIO_COMMUNICATION_PATH", "minio_communication"
)


class BucketExistsError(Exception):
    """
    Error bucket not existing in Minio.
    """


class MinioPathExistsError(Exception):
    """
    Error path to file not existing in Minio.
    """


def check_exist_bucket_validation(
    func: Callable[[VarArg(Any)], Any]
) -> Callable[[VarArg(Any)], Any]:
    """
    Validate input bucket name and raise error
    if bucket with that name doesn't exist.
    """

    def inner(*args: str) -> None:
        result = func(*args)
        if not result:
            LOGGER.error("%s bucket doesn't exist", args[0])
            raise BucketExistsError(f"{args[0]} bucket doesn't exist")

    return inner


def check_exist_path_validation(
    func: Callable[[str, str], List[str]]
) -> Callable[[VarArg(Any)], Any]:
    """
    Validate input file path and raise error
    if input path doesn't exist.
    """

    def inner(*args: str) -> List[str]:
        try:
            result = func(*args)
            if result:
                return result
            LOGGER.error("%s path doesn't exist", args[1])
            raise MinioPathExistsError(f"{args[1]} path doesn't exist")
        except error.S3Error as path_existing_error:
            LOGGER.error("%s path doesn't exist", args[1])
            raise MinioPathExistsError(
                f"{args[1]} path doesn't exist"
            ) from path_existing_error

    return inner


class MinioCommunicator:
    """
    Minio API object provides download files from Minio and upload files to.
    """

    client = None

    def __init__(self, minio_server: str, minio_root_user: str, minio_root_password: str) -> None:
        if not MinioCommunicator.client:
            self.create_client(minio_server, minio_root_user, minio_root_password)

    @classmethod
    def create_client(cls, minio_server, minio_root_user, minio_root_password) -> None:
        """
        Create connection with minio service.
        Returns:
            Return None
        """
        cls.client = Minio(
            endpoint=minio_server,
            access_key=minio_root_user,
            secret_key=minio_root_password,
            secure=False,
        )
        LOGGER.info(
            "MinIO client for %s was created successfully",
            minio_server,
        )

    def get_files_list(self, bucket: str, path: str) -> List[str]:
        """
        Check the path to the directory for existence.
        Args:
            bucket: bucket name, existing in minio
            path: directory path
        Returns:
            Return list of files in the current path
        """
        return [
            file.object_name
            for file in self.client.list_objects(
                bucket, recursive=True, prefix=str(path)
            )
        ]

    def download_file(self, bucket: str, path: str, local_path: Path) -> None:
        """
        Download file from minio to indicated local filename.
        Args:
            bucket: bucket name, existing in minio
            path: file path, existing in minio
            local_path: filename to save object
        Returns:
            Return None object
        """
        check_exist_bucket_validation(self.client.bucket_exists)(bucket)
        check_exist_path_validation(self.client.stat_object)(bucket, path)
        LOGGER.info(
            "Downloading file %s from bucket %s to %s",
            path,
            bucket,
            local_path,
        )
        self.client.fget_object(bucket, path, str(local_path))

    def download_directory(
        self, bucket: str, path: str, local_dir: Path
    ) -> None:
        """
        Download directory from minio to indicated local directory.
        Args:
            bucket: bucket name, existing in minio
            path: directory path, existing in minio
            local_dir: directory name to save objects
        Returns:
            Return None object
        """
        check_exist_bucket_validation(self.client.bucket_exists)(bucket)
        files = check_exist_path_validation(self.get_files_list)(bucket, path)
        if Path(path).suffix:
            LOGGER.error("%s is not a dir", path)
            raise ValueError(f"{path} is not a dir")
        if not local_dir.exists() or local_dir.is_file():
            local_dir.mkdir(parents=True)
        for file in files:
            self.download_file(bucket, file, local_dir / Path(file).name)

    def upload_file(self, bucket: str, path: str, local_path: Path) -> None:
        """
        Upload file to minio.
        Args:
            bucket: bucket name, existing in minio
            path: minio path to upload file
            local_path: local path to file to upload in minio
        Returns:
            Return None object
        """
        check_exist_bucket_validation(self.client.bucket_exists)(bucket)
        if not local_path.exists() or not local_path.suffix:
            LOGGER.error("file %s doesn't exist", local_path)
            raise FileExistsError(f"file {local_path} doesn't exist")
        LOGGER.info(
            "Uploading from file %s to %s/%s", local_path, bucket, path
        )
        self.client.fput_object(
            bucket, os.path.join(path, local_path), local_path
        )

    def upload_directory(
        self, bucket: str, path: str, local_dir: Path
    ) -> None:
        """
        Upload directory to minio.
        Args:
            bucket: bucket name, existing in minio
            path: minio path to upload file
            local_dir: local path to directory to upload in minio
        Returns:
            Return None object
        """
        check_exist_bucket_validation(self.client.bucket_exists)(bucket)
        if not local_dir.is_dir():
            LOGGER.error("%s is not a directory", local_dir)
            raise IsADirectoryError(f"{local_dir} is not a directory")
        if not local_dir.exists():
            LOGGER.error("%s doesn't exist", local_dir)
            raise NotADirectoryError(f"{local_dir} doesn't exist")
        LOGGER.info(
            "Uploading files from directory %s to %s/%s",
            local_dir,
            bucket,
            path,
        )
        for file in Path.iterdir(local_dir):
            self.upload_file(bucket, path, file)
