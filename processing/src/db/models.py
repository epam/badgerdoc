import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import settings

Base = declarative_base()
engine = sa.create_engine(
    settings.database_url,
    pool_use_lifo=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class DbPreprocessingTask(Base):  # type: ignore

    __tablename__ = "preprocessing_tasks"

    id = sa.Column(sa.Integer, primary_key=True)
    execution_id = sa.Column(sa.Integer)
    batch_id = sa.Column(sa.String(100))
    file_id = sa.Column(sa.Integer, nullable=False)
    pipeline_id = sa.Column(sa.Integer, nullable=False)
    status = sa.Column(sa.String(100))
    execution_args = sa.Column(sa.JSON(none_as_null=True))
