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
