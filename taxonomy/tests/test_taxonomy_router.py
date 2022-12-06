import pytest

from app.models import AssociationTaxonomyJob, Taxonomy
from app.taxonomy import services
from tests.override_app_dependency import TEST_HEADER


@pytest.mark.integration
def test_create_taxonomy_should_work(overrided_token_client, db_session):
    # given
    input_data = {
        "id": "123",
        "name": "some_name",
    }

    # when
    response = overrided_token_client.post(
        "/taxonomy",
        json=input_data,
        headers=TEST_HEADER,
    )

    # then
    assert response
    assert response.status_code == 201
    assert response.json()["id"] == input_data["id"]
    assert response.json()["name"] == input_data["name"]
    assert response.json()["version"] == 1

    taxonomy: Taxonomy = services.get_latest_taxonomy(
        db_session, input_data["id"]
    )

    assert taxonomy.id == input_data["id"]
    assert taxonomy.name == input_data["name"]
    assert taxonomy.version == 1
    assert taxonomy.latest


@pytest.mark.integration
def test_create_new_taxonomy_with_same_id_should_update_version(
    overrided_token_client, db_session
):
    # given
    input_data = {
        "id": "321",
        "name": "some_name",
    }
    overrided_token_client.post(
        "/taxonomy",
        json=input_data,
        headers=TEST_HEADER,
    )

    # when
    response = overrided_token_client.post(
        "/taxonomy",
        json=input_data,
        headers=TEST_HEADER,
    )

    # then
    assert response
    assert response.status_code == 201

    new_taxonomy: Taxonomy = services.get_latest_taxonomy(
        db_session, input_data["id"]
    )

    assert new_taxonomy.id == input_data["id"]
    assert new_taxonomy.name == input_data["name"]
    assert new_taxonomy.version == 2
    assert new_taxonomy.latest

    previous_taxonomy = services.get_second_latest_taxonomy(
        db_session, input_data["id"]
    )

    assert not previous_taxonomy.latest


@pytest.mark.integration
def test_should_return_latest_taxonomy(
    overrided_token_client, prepared_taxonomy_record_in_db: Taxonomy
):
    # given
    taxonomy_id = prepared_taxonomy_record_in_db.id
    # when
    response = overrided_token_client.get(
        "/taxonomy/{taxonomy_id}".format(taxonomy_id=taxonomy_id),
        headers=TEST_HEADER,
    )
    # then
    assert response.status_code == 200
    assert response.json()["id"] == prepared_taxonomy_record_in_db.id


@pytest.mark.integration
def test_should_return_taxonomy_by_id_and_version(
    prepare_two_taxonomy_records_with_same_id_in_db,
    overrided_token_client,
    taxonomy_orm_object,
):
    # given
    taxonomy_id = prepare_two_taxonomy_records_with_same_id_in_db[0].id
    version = prepare_two_taxonomy_records_with_same_id_in_db[0].version
    # when
    response = overrided_token_client.get(
        "/taxonomy/{taxonomy_id}/{version}".format(
            taxonomy_id=taxonomy_id,
            version=version,
        ),
        headers=TEST_HEADER,
    )
    # then
    assert response.status_code == 200
    assert response.json()["id"] == taxonomy_orm_object.id


@pytest.mark.integration
def test_should_associate_taxonomy_to_job(
    overrided_token_client,
    prepared_taxonomy_record_in_db: Taxonomy,
    db_session,
):
    # given
    taxonomy_id = prepared_taxonomy_record_in_db.id
    job_id = "123"
    # when
    response = overrided_token_client.post(
        "/taxonomy/{taxonomy_id}/link_to_job".format(
            taxonomy_id=taxonomy_id,
        ),
        json={"id": job_id},
        headers=TEST_HEADER,
    )
    # then
    assert response
    assert response.status_code == 201

    association: AssociationTaxonomyJob = (
        db_session.query(AssociationTaxonomyJob)
        .filter(AssociationTaxonomyJob.job_id == job_id)
        .first()
    )
    assert association
    assert association.taxonomy is prepared_taxonomy_record_in_db


@pytest.mark.integration
def test_should_associate_taxonomy_to_category(
    overrided_token_client,
    prepared_taxonomy_record_in_db: Taxonomy,
    db_session,
):
    # given
    request_body = [
        {
            "taxonomy_id": prepared_taxonomy_record_in_db.id,
            "taxonomy_version": prepared_taxonomy_record_in_db.version,
            "category_id": "123",
        }
    ]
    # when
    response = overrided_token_client.post(
        "/taxonomy/link_category",
        json=request_body,
        headers=TEST_HEADER,
    )
    # then
    assert response
    assert response.status_code == 201

    db_session.refresh(prepared_taxonomy_record_in_db)
    assert request_body[0]["category_id"] in [
        c.category_id for c in prepared_taxonomy_record_in_db.categories
    ]


@pytest.mark.integration
def test_should_update_taxonomy_in_db(
    overrided_token_client,
    prepared_taxonomy_record_in_db: Taxonomy,
    db_session,
    taxonomy_input_data,
):
    # given
    taxonomy_input_data["id"] = prepared_taxonomy_record_in_db.id
    taxonomy_input_data["name"] = "new_name"
    # when
    response = overrided_token_client.put(
        "/taxonomy",
        json=taxonomy_input_data,
        headers=TEST_HEADER,
    )
    # then
    assert response
    assert response.status_code == 200
    assert response.json()["name"] == taxonomy_input_data["name"]


@pytest.mark.integration
def test_should_delete_taxonomy_from_db(
    overrided_token_client,
    prepared_taxonomy_record_in_db: Taxonomy,
    db_session,
):
    # when
    response = overrided_token_client.delete(
        "/taxonomy/{taxonomy_id}".format(
            taxonomy_id=prepared_taxonomy_record_in_db.id,
        ),
        headers=TEST_HEADER,
    )
    # then
    assert response
    assert response.status_code == 204

    taxonomy = services.get_latest_taxonomy(
        db_session, prepared_taxonomy_record_in_db.id
    )
    assert taxonomy is None


@pytest.mark.integration
def test_should_delete_latest_taxonomy_from_db(
    prepare_two_taxonomy_records_with_same_id_in_db,
    overrided_token_client,
    taxonomy_orm_object,
    db_session,
):
    # given
    new_latest_taxonomy, taxonomy_to_delete, = sorted(
        prepare_two_taxonomy_records_with_same_id_in_db,
        key=lambda x: x.version,
    )
    assert taxonomy_to_delete.version > new_latest_taxonomy.version
    # when
    response = overrided_token_client.delete(
        "/taxonomy/{taxonomy_id}".format(
            taxonomy_id=taxonomy_to_delete.id,
        ),
        headers=TEST_HEADER,
    )
    # then
    assert response
    assert response.status_code == 204

    db_session.refresh(new_latest_taxonomy)
    assert new_latest_taxonomy.latest
