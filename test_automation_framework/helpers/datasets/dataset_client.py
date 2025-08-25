from __future__ import annotations

from helpers.base_client.base_client import BaseClient
import logging

logger = logging.getLogger(__name__)


class DatasetClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def search(
        self,
        page_num: int = 1,
        page_size: int = 100,
        filters: list[dict] | None = None,
        sorting: list[dict] | None = None,
    ) -> dict:
        payload = {
            "pagination": {"page_num": page_num, "page_size": page_size},
            "filters": filters or [],
            "sorting": sorting or [{"direction": "asc", "field": "name"}],
        }
        return self.post_json(
            "/assets/datasets/search", json=payload, headers=self._default_headers(content_type_json=True)
        )

    def search_files(
        self,
        dataset_id: int | None = None,
        page_num: int = 1,
        page_size: int = 15,
    ) -> dict:
        filters = []
        if dataset_id is not None:
            filters.append({"field": "datasets.id", "operator": "eq", "value": dataset_id})
        else:
            filters.append({"field": "original_name", "operator": "ilike", "value": "%%"})

        payload = {
            "pagination": {"page_num": page_num, "page_size": page_size},
            "filters": filters,
            "sorting": [{"direction": "desc", "field": "last_modified"}],
        }

        return self.post_json(
            "/assets/files/search", json=payload, headers=self._default_headers(content_type_json=True)
        )

    def create_dataset(self, name: str) -> dict:
        payload = {"name": name}
        resp = self.post_json("/assets/datasets", json=payload, headers=self._default_headers(content_type_json=True))
        logger.info(f"Created dataset {name}")
        return resp

    def delete_dataset(self, name: str) -> dict:
        payload = {"name": name}
        resp = self.delete_json("/assets/datasets", json=payload, headers=self._default_headers(content_type_json=True))
        logger.info(f"Deleted dataset {name}")
        return resp
