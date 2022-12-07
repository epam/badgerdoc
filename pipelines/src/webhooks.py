import urllib.parse
from typing import Any, Dict, Optional, Tuple, Union

from src import http_utils, log, schemas, service_token
from src.db import service

logger = log.get_logger(__file__)


def create_job_url(webhook: str, job_id: int) -> str:
    """Create url for the job_id for jobs microservice."""
    return urllib.parse.urljoin(webhook + "/", str(job_id))


def create_preprocessing_url(webhook: str, task_id: int) -> str:
    """Create url for the task_id fo processing microservice."""
    return urllib.parse.urljoin(webhook + "/", str(task_id))


def create_inference_url_and_body(
    webhook: str,
    job_id: int,
    task_status: schemas.Status,
) -> Union[Tuple[str, Dict[str, schemas.Status]], Tuple[None, None]]:
    """Creates url and body of jobs microservice webhook."""
    job_new_status = service.run_in_session(
        service.get_job_status_if_changed, job_id, task_status
    )
    if job_new_status is None:
        # means the status has not changed.
        return None, None
    url = create_job_url(webhook, job_id)
    body = {"status": job_new_status}
    return url, body


def create_preprocessing_url_and_body(
    webhook: str,
    task_id: int,
    task_status: schemas.Status,
) -> Tuple[str, Dict[str, schemas.Status]]:
    """Creates url and body of preprocessing microservice webhook."""
    url = create_preprocessing_url(webhook, task_id)
    body = {"status": task_status}
    return url, body


def send_webhook(
    url: str,
    body: Dict[str, Any],
    token: Optional[str] = None,
    tenant: Optional[str] = None,
) -> None:
    if token is None:
        token = service_token.get_service_token()
    if token is None:
        logger.error(
            f"Cannot receive service token. Webhook to url {url} "
            f"with body {body} wasn`t sent."
        )
        return
    headers = {"X-Current-Tenant": tenant, "Authorization": f"Bearer {token}"}
    http_utils.make_request_with_retry(url=url, body=body, headers=headers)
