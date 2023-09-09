import os
from typing import Dict, List, Optional, Set, Tuple, Union

import requests
from dotenv import find_dotenv, load_dotenv
from requests import ConnectionError, RequestException, Timeout

from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
    get_response,
    raise_request_exception,
)
from annotation.utils import get_service_uri

load_dotenv(find_dotenv())

ASSETS_SERVICE_HOST = get_service_uri("ASSETS_")
ASSETS_FILES_URL = f"{ASSETS_SERVICE_HOST}/files/search"
ASSETS_URL = f"{ASSETS_SERVICE_HOST}/datasets"
ASSETS_FILE_ID_FIELD = "id"
ASSETS_FILE_NAME_FIELD = "original_name"

FilesForDistribution = List[Dict[str, Union[int, List[int]]]]


def prepare_files_for_distribution(
    files_to_distribute: FilesForDistribution,
) -> FilesForDistribution:
    """
    Sort files by number of pages in descending order.
    """
    return sorted(
        files_to_distribute,
        key=lambda x: x["pages_number"],
        reverse=True,
    )


def get_files_info(
    files_ids: Set[Optional[int]],
    datasets_ids: Set[Optional[int]],
    tenant: str,
    token: str,
) -> List[Dict[str, int]]:
    files = files_ids.copy()

    files_info = get_response(
        ASSETS_FILE_ID_FIELD, list(files), ASSETS_FILES_URL, tenant, token
    )
    files_pages_info = [
        {"file_id": f[ASSETS_FILE_ID_FIELD], "pages_number": f["pages"]}
        for f in files_info
    ]

    datasets_pages_info = []
    for dataset_id in datasets_ids:
        dataset_files_info = get_dataset_info(dataset_id, tenant, token)
        dataset_pages_info = [
            {"file_id": f[ASSETS_FILE_ID_FIELD], "pages_number": f["pages"]}
            for f in dataset_files_info
            if f[ASSETS_FILE_ID_FIELD] not in files
        ]
        files.update(
            {dataset_file["file_id"] for dataset_file in dataset_pages_info}
        )
        datasets_pages_info.extend(dataset_pages_info)
    return prepare_files_for_distribution(
        files_pages_info + datasets_pages_info
    )


def get_dataset_info(dataset_id: int, tenant: str, token: str) -> List[dict]:
    try:
        dataset_files_info = requests.get(
            f"{ASSETS_URL}/{dataset_id}/files",
            headers={
                HEADER_TENANT: tenant,
                AUTHORIZATION: f"{BEARER} {token}",
            },
            timeout=5,
        )
    except (ConnectionError, RequestException, Timeout) as err:
        raise_request_exception(err)
    if dataset_files_info.status_code != 200:
        raise_request_exception(dataset_files_info.text)
    return dataset_files_info.json()


def get_file_names_by_request(
    file_ids: List[int], tenant: str, token: str
) -> Dict[int, str]:
    """
    Return dict of file_id and its name for provided
    file_ids.
    """
    files = get_response(
        ASSETS_FILE_ID_FIELD, file_ids, ASSETS_FILES_URL, tenant, token
    )
    return {f[ASSETS_FILE_ID_FIELD]: f[ASSETS_FILE_NAME_FIELD] for f in files}


def get_files_by_request(
    file_names: List[str], tenant: str, token: str
) -> Dict[int, str]:
    """
    Return files for provided file name.
    """
    files = get_response(
        ASSETS_FILE_NAME_FIELD, file_names, ASSETS_FILES_URL, tenant, token
    )
    return {f[ASSETS_FILE_ID_FIELD]: f[ASSETS_FILE_NAME_FIELD] for f in files}


def get_file_path_and_bucket(
    file_id: int, tenant: str, token: str
) -> Tuple[Optional[str], Optional[str]]:
    assets_response = get_response(
        ASSETS_FILE_ID_FIELD, [file_id], ASSETS_FILES_URL, tenant, token
    )
    if assets_response:
        return assets_response[0]["path"], assets_response[0]["bucket"]
    return None, None
