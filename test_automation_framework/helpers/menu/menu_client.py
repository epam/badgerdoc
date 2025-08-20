from __future__ import annotations
from helpers.base_client.base_client import BaseClient


class MenuClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url)
        self._token = token
        self._tenant = tenant

    def get_menu(self) -> list[dict]:
        resp = self.get(
            "/core/menu",
            headers={
                "Authorization": f"Bearer {self._token}",
                "X-Current-Tenant": self._tenant,
            },
        )
        return resp.json()
