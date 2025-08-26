from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
import logging
from helpers.base_client.base_client import BaseClient

logger = logging.getLogger(__name__)


class CategoryParent(BaseModel):
    name: str
    id: str
    type: str
    metadata: dict
    parent: Optional[str] = None
    data_attributes: List[dict] = []
    is_leaf: Optional[bool] = None


class Category(BaseModel):
    id: str
    name: str
    type: str
    metadata: dict
    parent: Optional[str] = None
    data_attributes: List[dict] = []
    parents: List[CategoryParent] = []
    is_leaf: bool


class Pagination(BaseModel):
    page_num: int
    page_offset: int
    page_size: int
    min_pages_left: int
    total: int
    has_more: bool


class CategoriesResponse(BaseModel):
    pagination: Pagination
    data: List[Category]


class CategoryCreateResponse(BaseModel):
    id: str
    name: str
    type: str
    metadata: dict
    parent: Optional[str] = None
    data_attributes: list[dict] = []
    editor: Optional[str] = None
    parents: Optional[list[dict]] = None
    is_leaf: Optional[bool] = None


class CategoriesClient(BaseClient):
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        super().__init__(base_url, token=token, tenant=tenant)

    def search_categories(
        self,
        page_num: int = 1,
        page_size: int = 15,
        filters: list[dict] | None = None,
        sorting: list[dict] | None = None,
    ) -> CategoriesResponse:
        payload = {
            "pagination": {"page_num": page_num, "page_size": page_size},
            "filters": filters or [],
            "sorting": sorting or [{"direction": "desc", "field": "name"}],
        }

        resp = self.post_json(
            "/annotation/categories/search",
            json=payload,
            headers=self._default_headers(content_type_json=True),
        )
        return CategoriesResponse.model_validate(resp)

    def create_category(
        self,
        category_id: str,
        name: str,
        category_type: str = "box",
        parent: str | None = None,
        metadata: dict | None = None,
        data_attributes: list[dict] | None = None,
    ) -> CategoryCreateResponse:
        payload = {
            "id": category_id,
            "name": name,
            "type": category_type,
            "parent": parent,
            "metadata": metadata or {"color": "#67DE61"},
            "data_attributes": data_attributes or [],
        }
        resp = self.post_json(
            "/annotation/categories",
            json=payload,
            headers=self._default_headers(content_type_json=True),
        )
        return CategoryCreateResponse.model_validate(resp)

    def delete_category(self, category_id: str) -> dict:
        payload = {"id": category_id}
        resp = self.delete_json(
            "/annotation/categories",
            json=payload,
            headers=self._default_headers(content_type_json=True),
        )
        logger.info(f"Deleted category {category_id}")
        return resp
