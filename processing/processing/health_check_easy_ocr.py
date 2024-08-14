# noqa: F821
import asyncio
from typing import List, Optional, Set

from badgerdoc_storage import storage as bd_storage
from fastapi import HTTPException

from processing.utils.aiohttp_utils import send_request
from processing.utils.logger import get_logger

logger = get_logger(__name__)

# Files health_check1 and health_check2 must be uploaded to minio
# Path to `health_check_files` accord to badgerdoc paths
# bucket: `post`, path: `files/file_id/file_id.pdf`
bucket = "post"

file_ids = {"health_check1": [1], "health_check2": [1, 2]}


async def health_check_preprocessing(
    model_url: str,
    languages: Optional[Set[str]] = None,
    tenant: Optional[str] = None,
) -> bool:
    """
    Run preprocessing for test paths and compare results to expected results
    The files and the expected results must exist.

    Path example to file: bucket, files/`file_id`/`file_id`.pdf
    Path example to expected results: bucket, files/`file_id`/expected
    """

    logger.info("Start %s health check", model_url)

    if not is_data_prepared():
        raise HTTPException(
            404,
            detail=f"Testing documents should exist. Check bucket `{bucket}`,"
            f"paths `{[f'files/{file_id}/' for file_id in file_ids]}`."
            "This directories should contain pdf file "
            "and folder with expected data",
        )

    await asyncio.gather(
        *(run_preprocessing(model_url, file, languages) for file in file_ids)
    )
    result = all(
        check_results(file, pages) for file, pages in file_ids.items()
    )
    for file, pages in file_ids.items():
        clear_data(file, pages, tenant)
    return result


def is_data_prepared() -> bool:
    raise NotImplementedError()
    # try:
    #    for file_id in file_ids:
    #        minio_client.stat_object(bucket, f"files/{file_id}/{file_id}.pdf")
    #        minio_client.stat_object(
    #            bucket, f"files/{file_id}/expected/1.json"
    #        )
    # except MinioException:
    #    return False
    # return True


async def run_preprocessing(
    model_url: str, file_id: str, languages: Optional[Set[str]] = None
) -> None:
    body = {
        "file": f"files/{file_id}/{file_id}.pdf",
        "bucket": bucket,
        "pages": None,
        "args": {"languages": languages},
    }
    await send_request(method="POST", url=model_url, json=body)


def check_results(file_id: str, pages: List[int]) -> bool:
    raise NotImplementedError()
    # for page in pages:
    #    try:
    #        test_page = minio_client.get_object(
    #            bucket, f"files/{file_id}/ocr/{page}.json"
    #        )
    #        expected_page = minio_client.get_object(
    #            bucket, f"files/{file_id}/expected/{page}.json"
    #        )
    #        if test_page.read() != expected_page.read():
    #            logger.error("Preprocessing works incorrect")
    #            return False
    #    except MinioException:
    #        logger.error("MinioException had happened
    # while checking easy-ocr health")
    #        return False
    #    finally:
    #        test_page.close()
    #        expected_page.close()
    #        test_page.release_conn()
    #        expected_page.release_conn()
    # logger.info("Preprocessing works correct")
    # return True


def clear_data(file_id: str, pages: List[int], tenant: str) -> None:
    for page in pages:
        bd_storage.get_storage(tenant).delete(
            f"files/{file_id}/ocr/{page}.json"
        )
