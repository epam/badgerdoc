from typing import Optional, Set

from db_example import Address, User, get_db
from fastapi import Depends, FastAPI
from filter_lib import (  # type: ignore
    Page,
    create_filter_model,
    form_query,
    map_request_to_filter,
    paginate,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

app = FastAPI()


class UserCreate(BaseModel):
    name: str
    fullname: str
    nickname: str


class UserOut(UserCreate):
    id: int

    class Config:
        orm_mode = True


class AddressCreate(BaseModel):
    email_address: str
    user_id: Optional[int] = None


class AddressOut(AddressCreate):
    id: int

    class Config:
        orm_mode = True


UserFilterModel = create_filter_model(User)
AddressFilterModel = create_filter_model(Address)


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
    request: UserFilterModel, session: Session = Depends(get_db)  # type: ignore # noqa
) -> Page[UserOut]:
    query = session.query(User)
    filter_args = map_request_to_filter(request.dict(), "User")  # type: ignore
    query, pagination = form_query(filter_args, query)
    return paginate([x for x in query], pagination)


@app.post("/addresses", tags=["addresses"])
def create_new_address(
    request: AddressCreate, session: Session = Depends(get_db)
) -> Set[str]:
    new_address = Address(
        email_address=request.email_address, user_id=request.user_id
    )
    session.add(new_address)
    session.commit()
    return {"New address created"}


@app.post(
    "/addresses/search", tags=["addresses"], response_model=Page[AddressOut]
)
def search_address(
    request: AddressFilterModel, session: Session = Depends(get_db)  # type: ignore # noqa
) -> Page[UserOut]:
    query = session.query(Address)
    filter_args = map_request_to_filter(request.dict(), "Address")  # type: ignore # noqa
    query, pagination = form_query(filter_args, query)
    return paginate([x for x in query], pagination)
