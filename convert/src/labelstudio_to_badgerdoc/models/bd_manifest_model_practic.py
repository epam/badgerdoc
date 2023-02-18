from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel


class DocumentLink(BaseModel):
    to: int
    category: str
    type: str


class Manifest(BaseModel):
    revision: str
    job_id: int
    user: Optional[str]
    pipeline: Optional[Any]
    date: Optional[str]
    pages: Dict[str, str]
    failed_validation_pages: List[int] = []
    validated: List[int] = []
    links_json: Optional[List[DocumentLink]]
    file: str
    bucket: str
    categories: List[Any] = []
