from __future__ import annotations
from typing import Any, Dict, List
import time
import logging

from helpers.base_client.base_client import BaseClient

logger = logging.getLogger(__name__)


class JobsClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def get_supported_pipelines(self) -> List[Dict[str, Any]]:
        return self.get_json("/jobs/pipelines/support", headers=self._default_headers())

    def get_pipeline(self, engine_resource: str) -> Dict[str, Any]:
        return self.get_json(f"/jobs/pipelines/{engine_resource}", headers=self._default_headers())

    def create_job(
        self,
        name: str,
        file_ids: list[int],
        pipeline_id: str,
        pipeline_engine: str,
        owners: list[str],
        datasets: list[int] | None = None,
        categories: list[str] | None = None,
        annotators: list[str] | None = None,
        validators: list[str] | None = None,
        previous_jobs: list[int] | None = None,
        revisions: list[int] | None = None,
        is_draft: bool = False,
        is_auto_distribution: bool = False,
        start_manual_job_automatically: bool = False,
        job_type: str = "ExtractionJob",
        pipeline_name: str | None = None,
    ):
        payload = {
            "name": name,
            "revisions": revisions or [],
            "datasets": datasets or [],
            "files": file_ids,
            "previous_jobs": previous_jobs or [],
            "type": job_type,
            "is_draft": is_draft,
            "is_auto_distribution": is_auto_distribution,
            "start_manual_job_automatically": start_manual_job_automatically,
            "categories": categories or [],
            "owners": owners or [],
            "annotators": annotators or [],
            "validators": validators or [],
            "pipeline_name": pipeline_name or pipeline_id,
            "pipeline_id": pipeline_id,
            "pipeline_engine": pipeline_engine,
        }

        return self.post_json(
            "/jobs/jobs/create_job", json=payload, headers=self._default_headers(content_type_json=True)
        )

    def get_job(self, job_id: int) -> Dict[str, Any]:
        return self.get_json(f"/jobs/jobs/{job_id}", headers=self._default_headers())

    def get_progress(self, job_id: int) -> Dict[str, Any]:
        return self.post_json(
            "/jobs/jobs/progress", json=[job_id], headers=self._default_headers(content_type_json=True)
        )

    def poll_until_finished(
        self,
        job_id: int,
        timeout_seconds: int = 120,
        interval_seconds: float = 1.0,
        backoff_factor: float = 1.5,
    ) -> Dict[str, Any]:
        start = time.monotonic()
        current_interval = interval_seconds

        logger.info(f"Polling job {job_id} until finished (timeout {timeout_seconds}s)")
        while True:
            elapsed = time.monotonic() - start
            if elapsed > timeout_seconds:
                raise TimeoutError(f"Job {job_id} not finished after {timeout_seconds}s")
            job_obj = self.get_job(job_id)
            status = job_obj.get("status") or job_obj.get("data", {}).get("status")
            logger.info(f"Polled job {job_id} status: {status}")

            if status and str(status).lower() in {"finished", "success", "completed"}:
                logger.info(f"Job {job_id} finished with status={status}")
                return job_obj
            try:
                progress = self.get_progress(job_id)
                if isinstance(progress, dict):
                    for k, v in progress.items():
                        if str(k) == str(job_id) and isinstance(v, dict):
                            fin = v.get("finished")
                            tot = v.get("total")
                            if fin is not None and tot is not None and fin >= tot:
                                logger.info("Progress shows job finished (finished>=total)")
                                return self.get_job(job_id)
            except Exception:
                logger.debug(f"Progress probe failed for job {job_id}; will retry")
            time.sleep(current_interval)
            current_interval = min(current_interval * backoff_factor, 10.0)
