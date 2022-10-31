"""Testing src/webhooks.py."""

from unittest.mock import patch

import src.schemas as schemas
import src.webhooks as webhooks


def test_create_inference_url_and_body():
    webhook = "http://test_service"
    job_id = 1
    task_status = schemas.Status.RUN
    status = schemas.JobStatus.RUN
    with patch(
        "src.webhooks.service.get_job_status_if_changed", return_value=status
    ):
        url, body = webhooks.create_inference_url_and_body(
            webhook=webhook, job_id=job_id, task_status=task_status
        )
    assert url == "http://test_service/1"
    assert body == {"status": status}


def test_create_preprocessing_url_and_body():
    webhook = "http://test_service"
    task_id = 1
    task_status = schemas.Status.RUN
    url, body = webhooks.create_preprocessing_url_and_body(
        webhook=webhook, task_id=task_id, task_status=task_status
    )
    assert url == "http://test_service/1"
    assert body == {"status": task_status}
