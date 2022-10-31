from pydantic import BaseModel


class ConnectionErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Connection error."},
        }


class NotFoundErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Resource was not found."},
        }
