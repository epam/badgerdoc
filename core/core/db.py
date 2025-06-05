import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Change the driver from psycopg2 to asyncpg
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


# Update return type annotation to AsyncGenerator
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = LOCAL_SESSION()  # Create a session instance
    try:
        yield session
    finally:
        await session.close()  # Need to await close() for async session
