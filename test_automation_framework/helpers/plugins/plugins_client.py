from typing import Any, Dict, List
import logging
from helpers.base_client.base_client import BaseClient


logger = logging.getLogger(__name__)


class PluginsClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def get_plugins(self) -> List[Dict[str, Any]]:
        return self.get_json("/core/plugins", headers=self._default_headers())

    def create_plugin(
        self,
        name: str,
        menu_name: str,
        url: str,
        version: str = "1",
        description: str = "",
        is_iframe: bool = True,
    ) -> dict:
        payload = {
            "name": name,
            "menu_name": menu_name,
            "description": description,
            "version": version,
            "url": url,
            "is_iframe": is_iframe,
        }

        # Enhanced headers to match the successful request exactly
        headers = self._default_headers(content_type_json=True)
        headers.update(
            {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "DNT": "1",
                "Origin": "http://demo.badgerdoc.com:8083",
                "Priority": "u=0",
                "Referer": "http://demo.badgerdoc.com:8083/",
                "Sec-GPC": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0",
            }
        )

        # Log the request for debugging
        logger.info(f"Creating plugin with payload: {payload}")
        logger.info(f"Using headers: {headers}")

        try:
            return self.post_json(
                "/core/plugins",
                json=payload,
                headers=headers,
            )
        except Exception as e:
            logger.error(f"Failed to create plugin: {e}")
            if hasattr(e, "body"):
                logger.error(f"Response body: {e.body}")
            raise

    def update_plugin(self, plugin_id: int, **fields) -> dict:
        return self.put_json(
            f"/core/plugins/{plugin_id}",
            json=fields,
            headers=self._default_headers(content_type_json=True),
        )

    def delete_plugin(self, plugin_id: int) -> dict:
        return self.delete_json(
            f"/core/plugins/{plugin_id}",
            headers=self._default_headers(content_type_json=True),
        )
