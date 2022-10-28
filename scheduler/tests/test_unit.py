from tests import testing_data

import pytest
from scheduler import exceptions, unit


def test_from_message_right():
    unit_ = unit.Unit.from_message(testing_data.right_message)
    assert unit_.id == "test_id_1"
    assert unit_.url == "test_url"
    assert unit_.body == {"args": "test_args"}
    assert unit_.tenant == "test_tenant"
    assert unit_.response_topic == "test_response_topic"


def test_from_message_wrong():
    with pytest.raises(exceptions.WrongSignature):
        unit_ = unit.Unit.from_message(testing_data.wrong_message)


def test_from_orm_unit_method(testing_unit_instance):
    unit_ = unit.Unit.from_orm(testing_unit_instance)
    assert unit_.id == "uid_1"
    assert unit_.url == "url_1"
