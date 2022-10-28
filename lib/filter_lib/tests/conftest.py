import pytest

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String)
    address = sa.Column(
        sa.Integer, sa.ForeignKey("addresses.id", use_alter=True)
    )
    email = sa.Column(sa.String)


class Address(Base):
    __tablename__ = "addresses"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    location = sa.Column(sa.String)
    owner = sa.Column(sa.Integer, sa.ForeignKey("users.id", use_alter=True))


@pytest.fixture(scope="function")
def get_session():
    test_db_url = "sqlite://"
    engine = sa.create_engine(test_db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
