from __future__ import annotations
from helpers.base_client.base_client import BaseClient


class MenuClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def get_menu(self) -> list[dict]:
        return self.get_json("/core/menu", headers=self._default_headers())
