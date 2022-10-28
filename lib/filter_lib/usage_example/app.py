from typing import Set

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from filter_lib import (
    Page,
    create_filter_model,
    form_query,
    map_request_to_filter,
    paginate,
)

from .db_example import User, get_db

app = FastAPI()


class UserCreate(BaseModel):
    name: str
    fullname: str
    nickname: str


class UserOut(BaseModel):
    nickname: str
    name: str
    fullname: str
    id: int

    class Config:
        orm_mode = True


UserFilterModel = create_filter_model(User)


@app.post("/users", tags=["users"])
def create_new_user(
    request: UserCreate, session: Session = Depends(get_db)
) -> Set[str]:
    new_user = User(
        name=request.name, fullname=request.fullname, nickname=request.nickname
    )
    session.add(new_user)
    session.commit()
    return {"New user created"}


@app.post("/users/search", tags=["users"], response_model=Page[UserOut])
def search_users(
    request: UserFilterModel, session: Session = Depends(get_db)  # type: ignore
) -> Page[UserOut]:
    query = session.query(User)
    filter_args = map_request_to_filter(request.dict(), "User")  # type: ignore
    query, pagination = form_query(filter_args, query)
    return paginate([x for x in query], pagination)
