import os.path
from tempfile import TemporaryDirectory
from typing import Iterator, Optional, Set

from fastapi import HTTPException
from minio.error import MinioException

from src.utils.logger import get_logger
from src.utils.minio_utils import MinioCommunicator

logger = get_logger(__name__)


def download_files(
    bucket: str, minio_path: str, save_dir: str, pages: Set[int]
) -> Iterator[str]:
    files_to_download = (f"{minio_path}/{page}.json" for page in sorted(pages))
    for file in files_to_download:
        save_path = os.path.join(save_dir, file.rsplit("/", maxsplit=1)[-1])
        logger.info("Downloading %s/%s to %s", bucket, file, save_path)
        try:
            MinioCommunicator().client.fget_object(
                bucket_name=bucket,
                object_name=file,
                file_path=save_path,
            )
        except MinioException as err:
            raise HTTPException(status_code=400, detail=str(err))
        yield save_path


def get_pages(bucket: str, path: str, pages: Optional[Set[int]]) -> Set[int]:
    if pages:
        return pages

    try:
        pages_in_minio = MinioCommunicator().client.list_objects(
            bucket, path, recursive=True
        )
    except MinioException as err:
        raise HTTPException(status_code=400, detail=str(err))

    return set(
        (
            page.object_name.rsplit("/", maxsplit=1)[-1][:-5]
            for page in pages_in_minio
        )
    )


def send_preprocess_result(  # TODO implement as coroutine
    bucket: str, file_id: int, pages: Optional[Set[int]]
) -> str:
    """
    Take result of preprocessing from minio:///bucket/path/ocr for each page,
    concatenate the data and return as a string
    """
    logger.info(
        "Start processing bucket: %s, file_id: %s, pages: %s",
        bucket,
        file_id,
        pages if pages else "all",
    )
    path = f"files/{file_id}/ocr"
    pages = get_pages(bucket, path, pages)

    with TemporaryDirectory() as tmp_dir:
        file_paths = download_files(bucket, path, tmp_dir, pages)
        data = []
        for file in file_paths:
            with open(file) as fin:
                data.append(fin.read())
    return f"[{' ,'.join(data)}]"
