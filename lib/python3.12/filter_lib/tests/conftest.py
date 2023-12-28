import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_utils import LtreeType

Base = declarative_base()

# Monkey-patching visit operation not supported by SQLite
SQLiteTypeCompiler.visit_LTREE = lambda *args, **kwargs: "LTREE"


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String)
    email = sa.Column(sa.String)
    addresses = relationship("Address", back_populates="user")


class Address(Base):
    __tablename__ = "addresses"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    location = sa.Column(sa.String)
    owner = sa.Column(sa.Integer, sa.ForeignKey("users.id", use_alter=True))
    user = relationship("User", back_populates="addresses")


class Category(Base):
    __tablename__ = "categories"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    tree = sa.Column(LtreeType, nullable=False)


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
