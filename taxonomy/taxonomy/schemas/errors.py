from pydantic import ConfigDict, BaseModel


class ConnectionErrorSchema(BaseModel):
    detail: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Error: Connection error."},
        }
    )


class BadRequestErrorSchema(BaseModel):
    detail: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Bad request."},
        }
    )


class NotFoundErrorSchema(BaseModel):
    detail: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Resource was not found."},
        }
    )
