import os
from typing import AsyncGenerator, Generator

import sqlalchemy
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(
    os.environ.get("POSTGRES_USER"),
    os.environ.get("POSTGRES_PASSWORD"),
    os.environ.get("POSTGRES_HOST"),
    os.environ.get("POSTGRES_PORT"),
    os.environ.get("POSTGRES_DB"),
)

LOCAL_SESSION = async_sessionmaker(
    bind=create_async_engine(SQLALCHEMY_DATABASE_URL),
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields a SQLAlchemy async session.

    Usage:
        @app.get("/example")
        async def example_route(session: AsyncSession = Depends(get_session)):
            # Use the session here

    The session is automatically closed when the request is complete.
    """
    session = LOCAL_SESSION()
    try:
        yield session
    finally:
        await session.close()


# We're keepeing the synchronous version for compatibility with existing code
# until filter_lib supports async sessions.

SQLALCHEMY_DATABASE_URL_SYNC = "postgresql://{0}:{1}@{2}:{3}/{4}".format(
    os.environ.get("POSTGRES_USER"),
    os.environ.get("POSTGRES_PASSWORD"),
    os.environ.get("POSTGRES_HOST"),
    os.environ.get("POSTGRES_PORT"),
    os.environ.get("POSTGRES_DB"),
)

LOCAL_SESSION_SYNC = sessionmaker(
    bind=sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL_SYNC)
)


def get_session_sync() -> Generator[Session, None, None]:
    """Dependency function that yields a SQLAlchemy session.
    Usage:
        @app.get("/example")
        def example_route(session: Session = Depends(get_session_sync)):
            # Use the session here
    The session is automatically closed when the request is complete.
    """
    session = LOCAL_SESSION_SYNC()
    try:
        yield session
    finally:
        session.close()
