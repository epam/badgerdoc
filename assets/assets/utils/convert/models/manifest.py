from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DocumentLink(BaseModel):
    to: int
    category: str
    type: str


class Manifest(BaseModel):
    revision: str
    job_id: int
    user: Optional[str] = None
    pipeline: Optional[Any] = None
    date: Optional[str] = None
    pages: Dict[str, str]
    failed_validation_pages: List[int] = []
    validated: List[int] = []
    links_json: Optional[List[DocumentLink]] = None
    file: str
    bucket: str
    categories: List[Any] = []
