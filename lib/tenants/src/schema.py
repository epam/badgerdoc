from typing import List

from pydantic import BaseModel


class TenantData(BaseModel):
    user_id: int
    tenant: str
    roles: List[str]
