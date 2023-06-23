from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict

import requests
from fastapi import HTTPException, status

from convert.config import settings
from convert.converters.coco.coco_import.convert import ConvertToBadgerdoc
from convert.converters.coco.exceptions import UploadLimitExceedError
from convert.converters.coco.models import coco
from convert.converters.coco.utils.common_utils import check_uploading_limit
from convert.converters.coco.utils.s3_utils import S3Manager, s3_download_files
from convert.logger import get_logger

LOGGER = get_logger(__file__)


def download_coco_from_aws(s3_data: coco.DataS3) -> S3Manager:
    """
    Establishes connect with s3 and downloads list of the files
    """
    try:
        check_uploading_limit(s3_data.files_keys)
    except UploadLimitExceedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    s3 = S3Manager(s3_data.aws_access_key_id, s3_data.aws_secret_access_key)
    s3_download_files(s3, s3_data.bucket_s3, s3_data.files_keys)
    return s3


def import_run(
    s3_data: coco.DataS3,
    token: str,
    job_id: int,
    current_tenant: str,
    import_format: str,
    body: Dict[str, Any],
) -> Dict[str, str]:
    """
    Prepare data for the conversion,
    download and upload dataset images, categories existence check,
    convert to another format asynchronously, upload results to the minio
    """
    import_formats = {"badgerdoc": ConvertToBadgerdoc}
    s3 = download_coco_from_aws(s3_data)
    converter = import_formats[import_format](
        Path(s3_data.files_keys[0]), s3_data, token, current_tenant
    )

    with ThreadPoolExecutor(max_workers=3) as executor:
        checking_category = executor.submit(converter.check_category)
        convert = executor.submit(converter.convert)
        download = executor.submit(converter.download_images, s3)

        annotation_by_image = download.result()
        categories = checking_category.result()
        convert.done()

    job_update_url = f"{settings.jobs_service_host}/jobs/{job_id}"
    body["categories"], body["files"] = list(categories), list(
        annotation_by_image.values()
    )
    requests.put(
        job_update_url,
        json=body,
        headers={"X-Current-Tenant": current_tenant, "Authorization": token},
    )
    converter.upload_annotations(
        job_id, s3_data.bucket_s3, annotation_by_image
    )
    return {
        "msg": f"Dataset was converted to {import_format} "
        f"format and upload to bucket {current_tenant}"
        f'path - job_id{job_id}"'
    }
