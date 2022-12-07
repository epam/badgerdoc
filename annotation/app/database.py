import os

import sqlalchemy
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv(find_dotenv())

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}".format(
    os.environ.get("POSTGRES_USER"),
    os.environ.get("POSTGRES_PASSWORD"),
    os.environ.get("POSTGRES_HOST"),
    os.environ.get("POSTGRES_PORT"),
    os.environ.get("POSTGRES_DB"),
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Ensure LTREE extensions is installed
with engine.connect() as conn:
    try:
        conn.execute(sqlalchemy.sql.text("CREATE EXTENSION LTREE"))
    except sqlalchemy.exc.ProgrammingError as err_:
        # Exctension installed, just skip error
        if "DuplicateObject" not in str(err_):
            raise err_


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
