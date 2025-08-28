from typing import List
import logging
from helpers.base_client.base_client import BaseClient

logger = logging.getLogger(__name__)


class ReportsClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def export_tasks(
        self,
        user_ids: List[str],
        date_from: str,
        date_to: str,
    ) -> str:
        payload = {
            "user_ids": user_ids,
            "date_from": date_from,
            "date_to": date_to,
        }
        resp = self.post(
            "/annotation/tasks/export",
            json=payload,
            headers=self._default_headers(content_type_json=True),
        )
        resp.raise_for_status()
        logger.info(f"Exported tasks for users={user_ids} from {date_from} to {date_to}")
        return resp.text
