from threading import Thread
from typing import Any, Dict
from urllib.error import HTTPError
from uuid import uuid4

from convert.coco_import.import_service import import_run
from convert.config import get_request_session, settings
from convert.logger import get_logger
from convert.models.coco import DataS3

LOGGER = get_logger(__file__)


def create_import_job(
    import_format: str,
    s3_data: DataS3,
    tenant_dependency: Dict[str, Any],
    current_tenant: str,
) -> Any:
    """
    Creates import job, starts the conversion in another thread
    """

    token = f"Bearer {tenant_dependency.__dict__.get('token', None)}"
    job_create_url = f"{settings.job_service_url}create_job/"
    headers = {"X-Current-Tenant": current_tenant, "Authorization": token}
    body = {
        "name": f"import_job_{uuid4()}",
        "type": "ImportJob",
        "import_source": s3_data.bucket_s3,
        "import_format": import_format,
        "owners": [tenant_dependency.__dict__.get("user_id")],
        "files": [],
        "categories": [],
    }
    session = get_request_session()
    response = session.post(url=job_create_url, json=body, headers=headers)
    response.raise_for_status()
    job_id = response.json().get("id")
    convert_response = Thread(
        target=import_run,
        args=(s3_data, token, job_id, current_tenant, import_format, body),
    )
    LOGGER.info("Convert is started")
    convert_response.start()
    return job_id
