import enum
from typing import List

from pydantic import BaseModel


class TenantData(BaseModel):
    token: str
    user_id: str
    roles: List[str]
    tenants: List[str]


class SupportedAlgorithms(str, enum.Enum):
    HS256 = "HS256"
    RS256 = "RS256"

    @classmethod
    def members(cls) -> List[str]:
        return [el for el in cls.__members__.keys()]
