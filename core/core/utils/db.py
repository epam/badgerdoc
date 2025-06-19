import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(
    os.environ.get("POSTGRES_USER"),
    os.environ.get("POSTGRES_PASSWORD"),
    os.environ.get("POSTGRES_HOST"),
    os.environ.get("POSTGRES_PORT"),
    os.environ.get("POSTGRES_DB"),
)

LOCAL_SESSION = async_sessionmaker(
    bind=create_async_engine(SQLALCHEMY_DATABASE_URL)
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = LOCAL_SESSION()
    try:
        yield session
    finally:
        await session.close()
