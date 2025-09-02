from __future__ import annotations
from helpers.base_client.base_client import BaseClient
import logging
from typing import List
import shutil
import uuid
from pathlib import Path
import httpx
from helpers.base_client.base_client import HTTPError

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

    @staticmethod
    def upload_temp_file(client, file_tracker, tmp_path, suffix="pdf"):
        data_dir = Path(__file__).parent.parent.parent / "data"
        original_file = data_dir / "multivitamin.pdf"
        unique_name = f"{uuid.uuid4().hex}.{suffix}"
        temp_file = tmp_path / unique_name
        shutil.copy(original_file, temp_file)
        result = client.upload_file(str(temp_file))
        file_info = result[0]
        assert file_info["status"] is True
        file_tracker[0].append(file_info)
        return file_info, temp_file

    def download_file(self, file_id: int) -> bytes:
        resp = self._client.get(
            f"{self.base_url}/assets/download?file_id={file_id}",
            headers=self._default_headers(),
            follow_redirects=False,
        )

        if resp.status_code >= 400:
            raise HTTPError(
                f"GET {resp.request.url} -> {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            )

        if resp.status_code == 302 and "location" in resp.headers:
            s3_resp = httpx.get(resp.headers["location"])
            s3_resp.raise_for_status()
            return s3_resp.content

        raise HTTPError(
            f"Unexpected response {resp.status_code} for file_id={file_id}",
            status_code=resp.status_code,
            body=resp.text,
        )
