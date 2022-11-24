import contextlib
from typing import Tuple
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from schemas import TaxonomyInputSchema
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.main import app
from app.models import Taxonomy
from app.taxonomy import services
from app.token_dependency import TOKEN
from tests.override_app_dependency import TEST_TENANTS, override


@pytest.fixture(scope="function")
def client() -> TestClient:
    client = TestClient(app)
    return client


@pytest.fixture
def overrided_token_client(client) -> TestClient:
    app.dependency_overrides[TOKEN] = override
    yield client
    app.dependency_overrides[TOKEN] = TOKEN


def clear_db():
    """
    Clear db
    reversed(Base.metadata.sorted_tables) makes
    it so children are deleted before parents.
    """
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        for table in reversed(Base.metadata.sorted_tables):
            con.execute(table.delete())
        sequences = con.execute("SELECT * FROM information_schema.sequences")
        for sequence in sequences:
            sequence_name = sequence[2]
            con.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1")
        trans.commit()


def close_session(gen):
    try:
        next(gen)
    except StopIteration:
        pass


@pytest.fixture(scope="module")
def db_session() -> Session:
    """Creates all tables on setUp, yields SQLAlchemy session and removes
    tables on tearDown.
    """
    from app.database import get_db

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    clear_db()
    gen = get_db()
    session = next(gen)

    yield session

    close_session(gen)


@pytest.fixture
def taxonomy_orm_object(taxonomy_input_data) -> Taxonomy:
    return Taxonomy(**taxonomy_input_data, **{"version": 1, "latest": True})


@pytest.fixture
def taxonomy_input_data():
    return dict(id=uuid4().hex, category_id=1, name="some_name")


@pytest.fixture
def prepared_taxonomy_record_in_db(
    taxonomy_input_data, db_session
) -> Taxonomy:
    return services.create_taxonomy_instance(
        db_session,
        TEST_TENANTS[0],
        TaxonomyInputSchema(**taxonomy_input_data),
        {"version": 1, "latest": True},
    )


@pytest.fixture
def prepare_two_taxonomy_records_with_same_id_in_db(
    taxonomy_input_data, db_session
) -> Tuple[Taxonomy, Taxonomy]:
    return (
        services.create_taxonomy_instance(
            db_session,
            TEST_TENANTS[0],
            TaxonomyInputSchema(**taxonomy_input_data),
            {"version": 1, "latest": False},
        ),
        services.create_taxonomy_instance(
            db_session,
            TEST_TENANTS[0],
            TaxonomyInputSchema(**taxonomy_input_data),
            {"version": 2, "latest": True},
        ),
    )
