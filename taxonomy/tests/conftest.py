import contextlib
import os
from copy import deepcopy
from typing import Generator, List, Tuple
from unittest.mock import patch
from uuid import uuid4

import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from alembic import command
from alembic.config import Config
from taxonomy.database import SQLALCHEMY_DATABASE_URL, Base, get_db, get_test_db_url
from taxonomy.main import app
from taxonomy.models import Taxon, Taxonomy
from taxonomy.schemas import CategoryLinkSchema, TaxonInputSchema, TaxonomyInputSchema
from taxonomy.taxon import services as taxon_services
from taxonomy.taxonomy import services as taxonomy_services
from taxonomy.token_dependency import TOKEN
from tests.override_app_dependency import TEST_TENANTS, override


@pytest.fixture
def client() -> TestClient:
    client = TestClient(app)
    return client


def clear_db(db_test_engine):
    """
    Clear db
    reversed(Base.metadata.sorted_tables) makes
    it so children are deleted before parents.
    """
    with contextlib.closing(db_test_engine.connect()) as con:
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


@pytest.fixture
def use_temp_env_var():
    with patch.dict(os.environ, {"USE_TEST_DB": "1"}):
        yield


@pytest.fixture
def db_test_engine():
    db_url = get_test_db_url(SQLALCHEMY_DATABASE_URL)
    test_db_engine = create_engine(db_url)
    yield test_db_engine


@pytest.fixture
def setup_test_db(use_temp_env_var, db_test_engine):

    # 1. drop existing database if there is one
    if database_exists(db_test_engine.url):
        drop_database(db_test_engine.url)

    # 2. create test database (empty)
    create_database(db_test_engine.url)

    # 3. Install 'ltree' extension
    with db_test_engine.connect() as conn:
        conn.execute(
            sqlalchemy.sql.text("CREATE EXTENSION IF NOT EXISTS ltree")
        )

    # 4. run 'alembic upgrade head'
    alembic_cfg = Config("alembic.ini")

    try:
        command.upgrade(alembic_cfg, "head")
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Got an Exception during migrations - {e}")

    yield


@pytest.fixture
def db_session(
    db_test_engine, setup_test_db
) -> Generator[Session, None, None]:
    """Creates all tables on setUp, yields SQLAlchemy session and removes
    tables on tearDown.
    """
    session_local = sessionmaker(bind=db_test_engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def taxonomy_orm_object(taxonomy_input_data) -> Taxonomy:
    return Taxonomy(**taxonomy_input_data, **{"version": 1, "latest": True})


@pytest.fixture
def taxonomy_input_data():
    return dict(id=uuid4().hex, name="some_name")


@pytest.fixture
def taxon_input_data(prepared_taxonomy_record_in_db):
    return {
        "id": None,
        "name": uuid4().hex,
        "taxonomy_id": prepared_taxonomy_record_in_db.id,
        "parent_id": None,
        "taxonomy_version": prepared_taxonomy_record_in_db.version,
    }


@pytest.fixture
def prepared_taxonomy_record_in_db(
    taxonomy_input_data, db_session
) -> Taxonomy:
    return taxonomy_services.create_taxonomy_instance(
        db_session,
        TEST_TENANTS[0],
        TaxonomyInputSchema(**taxonomy_input_data),
        {"version": 1, "latest": True},
    )


@pytest.fixture
def prepared_taxonomy_with_category_link(
    taxonomy_input_data, db_session
) -> Tuple[Taxonomy, CategoryLinkSchema]:
    taxonomy_version = 1
    taxonomy = taxonomy_services.create_taxonomy_instance(
        db_session,
        TEST_TENANTS[0],
        TaxonomyInputSchema(**taxonomy_input_data),
        {"version": taxonomy_version, "latest": True},
    )
    category_link = CategoryLinkSchema(
        category_id="123",
        job_id="321",
        taxonomy_id=taxonomy_input_data["id"],
        taxonomy_version=taxonomy_version,
    )
    taxonomy_services.bulk_create_relations_with_categories(
        db_session,
        {taxonomy_input_data["id"]: taxonomy_version},
        [category_link],
    )
    return taxonomy, category_link


@pytest.fixture
def prepare_common_tenant_taxonomy(db_session, taxonomy_input_data):
    taxonomy_input_data["id"] = "bcda"
    return taxonomy_services.create_taxonomy_instance(
        db_session,
        None,
        TaxonomyInputSchema(**taxonomy_input_data),
        {"version": 1, "latest": True},
    )


@pytest.fixture
def prepare_other_tenant_taxonomy(db_session, taxonomy_input_data):
    taxonomy_input_data["id"] = "abcd"
    return taxonomy_services.create_taxonomy_instance(
        db_session,
        TEST_TENANTS[1],
        TaxonomyInputSchema(**taxonomy_input_data),
        {"version": 1, "latest": True},
    )


@pytest.fixture
def prepared_taxon_entity_in_db(
    taxon_input_data,
    db_session,
) -> Taxon:
    return taxon_services.add_taxon_db(
        db_session,
        TaxonInputSchema(**taxon_input_data),
        TEST_TENANTS[0],
    )


@pytest.fixture
def prepare_two_taxonomy_records_with_same_id_in_db(
    taxonomy_input_data, db_session
) -> Tuple[Taxonomy, Taxonomy]:
    return (
        taxonomy_services.create_taxonomy_instance(
            db_session,
            TEST_TENANTS[0],
            TaxonomyInputSchema(**taxonomy_input_data),
            {"version": 1, "latest": False},
        ),
        taxonomy_services.create_taxonomy_instance(
            db_session,
            TEST_TENANTS[0],
            TaxonomyInputSchema(**taxonomy_input_data),
            {"version": 2, "latest": True},
        ),
    )


@pytest.fixture
def prepare_two_taxons_different_names(
    taxon_input_data,
    db_session,
) -> List[Taxon]:
    second_taxon = deepcopy(taxon_input_data)
    second_taxon["name"] = uuid4().hex
    return [
        taxon_services.add_taxon_db(
            db_session,
            TaxonInputSchema(**taxon_data),
            TEST_TENANTS[0],
        )
        for taxon_data in [taxon_input_data, second_taxon]
    ]


@pytest.fixture
def prepare_three_taxons_parent_each_other(
    db_session, taxon_input_data
) -> List[Taxon]:

    first_taxon = deepcopy(taxon_input_data)
    first_id = uuid4().hex
    first_taxon["id"] = first_id
    first_taxon["name"] = first_id

    second_taxon = deepcopy(taxon_input_data)
    second_id = uuid4().hex
    second_taxon["id"] = second_id
    second_taxon["name"] = second_id
    second_taxon["parent_id"] = first_taxon["id"]

    third_taxon = deepcopy(taxon_input_data)
    third_id = uuid4().hex
    third_taxon["id"] = third_id
    third_taxon["name"] = third_id
    third_taxon["parent_id"] = second_id

    return [
        taxon_services.add_taxon_db(
            db_session,
            TaxonInputSchema(**taxon),
            TEST_TENANTS[0],
        )
        for taxon in [first_taxon, second_taxon, third_taxon]
    ]


@pytest.fixture
def prepared_taxon_hierarchy(
    taxon_input_data, db_session, db_test_engine
) -> Generator[List[Taxon], None, None]:
    """
    Implement following structure:
        Europe.West.Germany.Hessen.Frankfurt.Sachsenhausen.Bahnhof
        Europe.West.Italy.Genoa.Castelletto
        Asia.South.China.Macao.Island.Macau_tower
    """

    path_1 = "Europe.West.Germany.Hessen.Frankfurt.Bahnhof".split(".")
    path_2 = "Europe.West.Italy.Genoa.District12.Street12".split(".")
    path_3 = "Asia.South.China.Mokao.Island.Macau_tower".split(".")

    seen = set()
    taxon_input_dataset = []
    for path in (path_1, path_2, path_3):
        for step in range(len(path)):
            if path[step] in seen:
                continue
            seen.add(path[step])

            if step == 0:
                parent_id = None
            else:
                parent_id = path[step - 1]

            taxon_data = taxon_input_data.copy()
            taxon_data["parent_id"] = parent_id
            taxon_data["id"] = path[step]
            taxon_data["name"] = path[step]
            taxon_input_dataset.append(taxon_data)

    taxons = [
        taxon_services.add_taxon_db(
            db_session,
            TaxonInputSchema(**taxon),
            TEST_TENANTS[0],
        )
        for taxon in taxon_input_dataset
    ]
    yield taxons
    # todo rework function to delete only needed items to avoid impact for
    #  other testcases in parallel run.
    clear_db(db_test_engine)


@pytest.fixture
def other_tenants_taxon(db_session, prepare_other_tenant_taxonomy):
    input_data = {
        "id": "madagascar",
        "name": "madagascar",
        "taxonomy_id": prepare_other_tenant_taxonomy.id,
        "parent_id": None,
        "taxonomy_version": prepare_other_tenant_taxonomy.version,
    }
    yield taxon_services.add_taxon_db(
        db_session,
        TaxonInputSchema(**input_data),
        TEST_TENANTS[1],
    )


@pytest.fixture
def common_taxon(db_session, prepare_common_tenant_taxonomy):
    input_data = {
        "id": "australia",
        "name": "australia",
        "taxonomy_id": prepare_common_tenant_taxonomy.id,
        "parent_id": None,
        "taxonomy_version": prepare_common_tenant_taxonomy.version,
    }
    yield taxon_services.add_taxon_db(
        db_session,
        TaxonInputSchema(**input_data),
        None,
    )


@pytest.fixture
def overrided_token_client(
    client, db_session
) -> Generator[TestClient, None, None]:

    app.dependency_overrides[TOKEN] = override
    app.dependency_overrides[get_db] = lambda: db_session
    yield client
    app.dependency_overrides[TOKEN] = TOKEN
