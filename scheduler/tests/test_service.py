from scheduler.db import models, service
from unittest import mock


def test_add_into_db(testing_session, testing_unit_instance):
    service.add_into_db(testing_session, testing_unit_instance)
    instance = testing_session.get(models.Unit, testing_unit_instance.id)

    assert isinstance(instance, models.Unit)
    assert instance.id == testing_unit_instance.id


def test_get_unit_by_id(testing_session, testing_unit_instance):
    testing_session.add(testing_unit_instance)
    testing_session.flush()
    testing_session.commit()
    instance = service.get_unit_by_id(testing_session, testing_unit_instance.id)

    assert isinstance(instance, models.Unit)
    assert instance.id == testing_unit_instance.id


def test_update_instance_by_id(testing_session, testing_unit_instance):
    testing_session.add(testing_unit_instance)
    service.update_instance_by_id(
        testing_session,
        models.Unit,
        testing_unit_instance.id,
        {"url": "new_url", "result": "new_result"},
    )
    instance = testing_session.get(models.Unit, testing_unit_instance.id)

    assert isinstance(instance, models.Unit)
    assert instance.id == testing_unit_instance.id
    assert instance.url == "new_url"
    assert instance.result == "new_result"
