from __future__ import annotations
from typing import Any, Optional
import httpx
import time
import logging

logger = logging.getLogger(__name__)


class HTTPError(RuntimeError):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        body: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class BaseClient:
    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        rel_path = path if path.startswith("/") else "/" + path
        start = time.perf_counter()
        try:
            resp = self._client.request(method, rel_path, **kwargs)
            resp.raise_for_status()
            logger.debug(
                f"HTTP {method} {self.base_url}{rel_path} -> {resp.status_code} in {time.perf_counter() - start:.3f}s"
            )
            return resp
        except httpx.HTTPStatusError as exc:
            resp = exc.response
            logger.error(
                f"Bad response: {resp.status_code} for {method} {self.base_url}{rel_path} - body: {resp.text[:500]}"
            )
            raise HTTPError(
                f"{method} {self.base_url}{rel_path} -> {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            ) from exc
        except httpx.RequestError as exc:
            logger.exception(f"Request failed: {method} {self.base_url}{rel_path}")
            raise HTTPError(f"request failed: {method} {self.base_url}{rel_path}") from exc

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("DELETE", path, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BaseClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
