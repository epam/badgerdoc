from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated


class FieldRole(str, Enum):
    role = "role"


class OperatorRole(str, Enum):
    eq = "eq"


class Roles(str, Enum):
    role = "role-annotator"


class FilterRole(BaseModel):
    field: FieldRole
    operator: OperatorRole
    value: Roles


class OperatorUserUserID(str, Enum):
    like = "in"


class FieldUserUserID(str, Enum):
    id = "id"


class FilterUserUserID(BaseModel):
    field: FieldUserUserID
    operator: OperatorUserUserID
    value: List[str]


class FieldUserUserName(str, Enum):
    name = "name"


class OperatorUserUserName(str, Enum):
    like = "like"


class FilterUserUserName(BaseModel):
    field: FieldUserUserName
    operator: OperatorUserUserName
    value: Annotated[str, StringConstraints(min_length=1)]  # type: ignore


class Users(BaseModel):
    filters: Optional[
        List[Union[FilterUserUserName, FilterUserUserID, FilterRole]]
    ] = None

