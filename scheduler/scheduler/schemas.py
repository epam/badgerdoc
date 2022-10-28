from pydantic import BaseModel


class StatusOut(BaseModel):
    status: str
