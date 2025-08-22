from __future__ import annotations
from helpers.base_client.base_client import BaseClient
import logging

logger = logging.getLogger(__name__)


class FileClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url)
        self._token = token
        self._tenant = tenant

    def upload_file(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            files = {"files": (file_path.split("/")[-1], f, "application/pdf")}
            resp = self.post(
                "/assets/files",
                files=files,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "X-Current-Tenant": self._tenant,
                },
            )
        logger.info(f"Uploaded file {file_path}")
        return resp.json()

    def delete_files(self, ids: list[int]) -> dict:
        resp = self.delete(
            "/assets/files",
            json={"objects": ids},
            headers={
                "Authorization": f"Bearer {self._token}",
                "X-Current-Tenant": self._tenant,
                "Content-Type": "application/json",
            },
        )
        logger.info(f"Deleted file {ids}")
        return resp.json()

    def search_files(
        self,
        page_num: int = 1,
        page_size: int = 15,
        filters: list[dict] | None = None,
    ) -> dict:
        payload = {
            "pagination": {"page_num": page_num, "page_size": page_size},
            "filters": filters or [{"field": "original_name", "operator": "ilike", "value": "%%"}],
            "sorting": [{"direction": "desc", "field": "last_modified"}],
        }
        resp = self.post(
            "/assets/files/search",
            json=payload,
            headers={
                "Authorization": f"Bearer {self._token}",
                "X-Current-Tenant": self._tenant,
                "Content-Type": "application/json",
            },
        )
        return resp.json()
