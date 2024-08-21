import os.path
from tempfile import TemporaryDirectory
from typing import Iterator, Optional, Set

from badgerdoc_storage import storage as bd_storage

from processing.utils.logger import get_logger

logger = get_logger(__name__)


def download_files(
    bucket: str, minio_path: str, save_dir: str, pages: Set[int]
) -> Iterator[str]:
    files_to_download = (f"{minio_path}/{page}.json" for page in sorted(pages))
    for file in files_to_download:
        save_path = os.path.join(save_dir, file.rsplit("/", maxsplit=1)[-1])
        logger.info("Downloading %s/%s to %s", bucket, file, save_path)
        bd_storage.get_storage(bucket).download(
            target_path=file,
            file=save_path,
        )
        yield save_path


def get_pages(tenant: str, path: str, pages: Optional[Set[int]]) -> Set[int]:
    if pages:
        return pages
    pages = bd_storage.get_storage(tenant).list_objects(path, recursive=True)
    return set(
        (page.object_name.rsplit("/", maxsplit=1)[-1][:-5] for page in pages)
    )


def send_preprocess_result(  # TODO implement as coroutine
    tenant: str, file_id: int, pages: Optional[Set[int]]
) -> str:
    """
    Take result of preprocessing from minio:///bucket/path/ocr for each page,
    concatenate the data and return as a string
    """
    logger.info(
        "Start processing bucket: %s, file_id: %s, pages: %s",
        tenant,
        file_id,
        pages if pages else "all",
    )
    path = f"files/{file_id}/ocr"
    pages = get_pages(tenant, path, pages)

    with TemporaryDirectory() as tmp_dir:
        file_paths = download_files(tenant, path, tmp_dir, pages)
        data = []
        for file in file_paths:
            with open(file) as fin:
                data.append(fin.read())
    return f"[{' ,'.join(data)}]"
