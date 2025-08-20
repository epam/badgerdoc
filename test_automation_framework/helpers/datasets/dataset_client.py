from __future__ import annotations
from helpers.base_client.base_client import BaseClient


class DatasetClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url)
        self._token = token
        self._tenant = tenant

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
        resp = self.post(
            "/assets/datasets/search",
            json=payload,
            headers={
                "Authorization": f"Bearer {self._token}",
                "X-Current-Tenant": self._tenant,
                "Content-Type": "application/json",
            },
        )
        return resp.json()

    def search_files(
        self,
        dataset_id: int | None = None,
        page_num: int = 1,
        page_size: int = 15,
    ) -> dict:
        """
        Fetch files. If dataset_id is provided, filter by dataset.
        Otherwise, fetch all files.
        """
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
