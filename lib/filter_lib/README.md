# filter_lib

Library for filtering and sorting sqlalchemy entities using Pydantic models

## How to use
Create your model for filtration and sorting from your database entities by using `create_filter_model()` function:

```Python
from filter_lib import create_filter_model
from usage_example.db_example import User

UserFilterModel = create_filter_model(User)
```
This will get all fields from `User` model, and you will be able to sort and filter through those fields.
If yot want to exclude some fields, use optional `exclude` argument:

```Python
from filter_lib import create_filter_model
from usage_example.db_example import User

UserFilterModel = create_filter_model(User, exclude=["id", "name"])
```
Then provide this model as a request model in your FastAPI endpoint:

```
@app.post("/users/search", tags=["users"])
def search_users(request: UserFilterModel, session: Session = Depends(get_db)):
```
Now you are able to see that generated model in FastAPI `docs`.
![alt text](https://i.ibb.co/ZYPYjcd/Screenshot-from-2021-09-23-00-27-02.png)


To apply filters and sorts use functions `map_request_to_filter` and `form_query` with your model:
```Python
from filter_lib import (
    create_filter_model,
    map_request_to_filter,
    form_query,
    paginate,
    Page
)

...
UserFilterModel = create_filter_model(User)

class UserOut(BaseModel):
    nickname: str
    name: str
    fullname: str
    id: int

    class Config:
        orm_mode = True



@app.post("/users/search", tags=["users"], response_model=Page[UserOut])
def search_users(request: UserFilterModel, session: Session = Depends(get_db)) -> Page[UserOut]:
    query = session.query(User)
    filter_args = map_request_to_filter(request.dict(), "User")
    query, pagination = form_query(filter_args, query)
    return paginate(query.all(), pagination)
```
`response_model=Page[UserOut]` Generates response example for swagger docs.

This part `filter_args = map_request_to_filter(request.dict(), "User")` will parse request dict into filter and sort args
for function `form_query`.
Note that you need to explicitly provide model name in `str` format for `map_request_to_filter` function. You can do it
like in provided example or `filter_args = map_request_to_filter(request.dict(), User.__name__)`

It's necessary for all queries, especially with several models like  `session.query(User, Address)`.

This part `query, pagination = form_query(filter_args, query)` will override your query and apply all filters and sorts to it.
It returns modified query and namedtuple with pagination params.

Finally `paginate(query.all(), pagination)` transforms sequence of your query's items and pagination params into `Page` view.

Function `paginate` takes sequence of items as first arg, so you can use it like in example with `query.all()` or something
like `[el for el in query]` etc. Second arg should be a namedtuple returned by `form_query` function.

Quick example:

```Python
# db_example.py
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

Base = declarative_base()

DATABASE_URL = "postgresql+psycopg2://admin:admin@localhost/db_for_usage_example"  # Database should be Postgres
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)

    addresses = relationship(
        "Address", back_populates="user", cascade="all, delete, delete-orphan"
    )


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="addresses")


def get_db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


Base.metadata.create_all(engine)


```

```Python
# app.py
from typing import Set

from fastapi import Depends, FastAPI
from filter_lib import (
    Page,
    create_filter_model,
    form_query,
    map_request_to_filter,
    paginate,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from python_base.filter_lib.usage_example.db_example import User, get_db


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
    request: UserFilterModel, session: Session = Depends(get_db)
) -> Page[UserOut]:
    query = session.query(User)
    filter_args = map_request_to_filter(request.dict(), "User")
    query, pagination = form_query(filter_args, query)
    return paginate(query.all(), pagination)
```

Available filter operations:
- ``match``
- ``is_null``
- ``is_not_null``
- ``eq``
- ``ne``
- ``gt``
- ``lt``
- ``ge``
- ``le``
- ``like``
- ``ilike``
- ``not_ilike``
- ``in``
- ``not_in``
- ``any``
- ``not_any``

Available sort orders:
- ``asc``
- ``desc``

Example:
![alt text](https://i.ibb.co/5M4RN43/Screenshot-from-2021-09-23-01-23-33.png)
This will return all Users with ids greater than 5 and less than 10 sorted by id in desc direction:
![alt text](https://i.ibb.co/86dzS6J/Screenshot-from-2021-09-23-01-27-22.png)
