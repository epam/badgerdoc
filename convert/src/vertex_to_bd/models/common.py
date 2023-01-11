from __future__ import annotations

from pydantic import BaseModel


class S3Path(BaseModel):
    bucket: str
    path: str
