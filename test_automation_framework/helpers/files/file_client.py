from __future__ import annotations
from helpers.base_client.base_client import BaseClient
import logging
from typing import List

logger = logging.getLogger(__name__)


class FileClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def upload_file(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            files = {"files": (file_path.split("/")[-1], f, "application/pdf")}
            resp = self.post("/assets/files", files=files, headers=self._default_headers())
        logger.info(f"Uploaded file {file_path}")
        return resp.json()

    def delete_files(self, ids: List[int]) -> dict:
        resp = self.delete_json(
            "/assets/files",
            json={"objects": ids},
            headers=self._default_headers(content_type_json=True),
        )
        logger.info(f"Deleted file {ids}")
        return resp

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
        return self.post_json(
            "/assets/files/search", json=payload, headers=self._default_headers(content_type_json=True)
        )

    def move_files(self, name: str, objects: list) -> dict:
        payload = {"name": name, "objects": objects}
        resp = self.post_json(
            "/assets/datasets/bonds", json=payload, headers=self._default_headers(content_type_json=True)
        )
        logger.info(f"Moved object {objects} to the dataset {name}")
        return resp
