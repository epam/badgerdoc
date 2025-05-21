import os

import sqlalchemy
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(find_dotenv())

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}".format(
    os.environ.get("POSTGRES_USER"),
    os.environ.get("POSTGRES_PASSWORD"),
    os.environ.get("POSTGRES_HOST"),
    os.environ.get("POSTGRES_PORT"),
    os.environ.get("POSTGRES_DB"),
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)


def init_ltree_ext() -> None:
    """Ensure LTREE extensions is installed"""
    with engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.sql.text("CREATE EXTENSION LTREE"))
        except sqlalchemy.exc.ProgrammingError as err_:
            # Exctension installed, just skip error
            if "DuplicateObject" not in str(err_):
                raise


def todict(obj):
    """Return the object's dict excluding private attributes,
    sqlalchemy state and relationship attributes.
    """
    excl = ("_sa_adapter", "_sa_instance_state")
    return {
        k: v
        for k, v in vars(obj).items()
        if not k.startswith("_") and not any(hasattr(v, a) for a in excl)
    }


class Base:
    def __repr__(self):
        params = ", ".join(f"{k}={v}" for k, v in todict(self).items())
        return f"{self.__class__.__name__}({params})"


Base = declarative_base(cls=Base)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
