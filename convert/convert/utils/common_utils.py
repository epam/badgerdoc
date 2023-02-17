import os
from typing import Any, Dict, List
from zipfile import ZipFile

from convert.config import minio_client, settings
from convert.exceptions import UploadLimitExceedError


def check_uploading_limit(files_list: List[str]) -> Any:
    """
    The function compares count of the files with definite limit
    Args:
        files_list: list of the files
    Raise:
    """
    limit = settings.uploading_limit
    if len(files_list) > limit:
        raise UploadLimitExceedError(
            f"Current limit for uploading is {settings.uploading_limit}!"
        )


def add_to_zip_and_local_remove(file: str, zip_file: ZipFile) -> None:
    """
    Write file to zip and remove it locally
    """
    zip_file.write(file)
    os.remove(file)


def get_headers(token: str, tenant: str) -> Dict[str, str]:
    return {"X-Current-Tenant": tenant, "Authorization": token}
