from unittest.mock import Mock

from pytest import mark

from src import crud
from src.crud import get_instance, get_latest_model
from src.db import Basement, Model, StatusEnum, Training
from src.schemas import BasementBase
from tests.test_utils import TEST_LIMITS
from tests.utils import create_expected_models, delete_date_field, row_to_dict

GET_BASEMENT = Basement(
    id="base_id", name="basement_name", gpu_support=True, limits=TEST_LIMITS
)
GET_TRAINING = Training(id=1, basement=GET_BASEMENT.id, name="training_name")
GET_LATEST_MODELS = [
    Model(id="model_1", basement=GET_BASEMENT.id, latest=False, version=1),
    Model(id="model_1", basement=GET_BASEMENT.id, latest=True, version=2),
]


def test_is_id_existing_queries_db_and_calls_filter():
    session = Mock()
    mocked = Mock()
    session.query.return_value = mocked
    crud.is_id_existing(session, Basement, "id")
    session.query.assert_called_once_with(Basement)
    mocked.filter.assert_called_once()


def test_create_instance_calls_add_and_commit_and_returns_id():
    session = Mock()
    basement = BasementBase(
        id="id", name="name", gpu_support=True, limits=TEST_LIMITS
    )
    crud.create_instance(session, Basement, basement, "author", "tenant")
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_get_instance_queries_db_calls_get_and_returns_result_of_get():
    session = Mock()
    mocked_query = Mock()
    session.query.return_value = mocked_query
    mocked_query.get.return_value = "expected"
    assert crud.get_instance(session, Basement, "id") == "expected"
    session.query.assert_called_once_with(Basement)
    mocked_query.get.assert_called_once_with("id")


def test_modify_instance_calls_commit():
    session = Mock()
    basement = BasementBase(
        id="id", name="name", gpu_support=True, limits=TEST_LIMITS
    )
    crud.get_instance = Mock(return_value="expected")
    crud.modify_instance(session, Basement, basement)
    session.commit.assert_called_once()
    session.refresh.assert_called_once()


def test_delete_instance_calls_delete_and_commit():
    session = Mock()
    assert crud.delete_instance(session, "instance") is None
    session.delete.assert_called_once_with("instance")
    session.commit_assert_called_once()


def test_modify_status_from_ready_to_deployed():
    session = Mock()
    model = Model(
        id="id",
        name="name",
        basement="basement",
        data_path=None,
        configuration_path=None,
        categories=["category"],
        status="ready",
        created_by="author",
        created_at="2021-11-09T17:09:43.101004",
        tenant="tenant",
    )
    assert crud.modify_status(session, model, "ready", "deployed") is None
    assert model.status == "deployed"
    session.commit_assert_called_once()


def test_modify_status_from_deployed_to_ready():
    session = Mock()
    model = Model(
        id="id",
        name="name",
        basement="basement",
        data_path=None,
        configuration_path=None,
        categories=["category"],
        status="deployed",
        created_by="author",
        created_at="2021-11-09T17:09:43.101004",
        tenant="tenant",
    )
    assert crud.modify_status(session, model, "deployed", "ready") is None
    assert model.status == "ready"
    session.commit_assert_called_once()


def test_modify_status_from_ready_to_ready_does_not_call_anything():
    session = Mock()
    model = Model(
        id="id",
        name="name",
        basement="basement",
        data_path=None,
        configuration_path=None,
        categories=["category"],
        status="ready",
        created_by="author",
        created_at="2021-11-09T17:09:43.101004",
        tenant="tenant",
    )
    assert crud.modify_status(session, model, "ready", "ready") is None
    assert model.status == "ready"
    session.commit_assert_not_called()


def test_modify_status_from_deployed_to_deployed_does_not_call_anything():
    session = Mock()
    model = Model(
        id="id",
        name="name",
        basement="basement",
        data_path=None,
        configuration_path=None,
        categories=["category"],
        status="deployed",
        created_by="author",
        created_at="2021-11-09T17:09:43.101004",
        tenant="tenant",
    )
    assert crud.modify_status(session, model, "deployed", "deployed") is None
    assert model.status == "deployed"
    session.commit_assert_not_called()


@mark.integration
def test_get_training_instance_from_db(prepare_db_model) -> None:
    """Tests that get_instance works correctly in integration with database."""
    training_db = get_instance(prepare_db_model, Training, GET_TRAINING.id)
    assert training_db.id == GET_TRAINING.id
    assert training_db.name == GET_TRAINING.name
    assert training_db.basement == GET_BASEMENT.id


@mark.integration
@mark.parametrize(
    ["model_id", "expected_result"],
    [
        (
            GET_LATEST_MODELS[0].id,
            create_expected_models(
                latest=True,
                version=GET_LATEST_MODELS[1].version,
                basement_id=GET_LATEST_MODELS[0].basement,
                model_id=GET_LATEST_MODELS[0].id,
                status=StatusEnum.READY,
            ),
        ),
        (
            "not_existing_id",
            None,
        ),
    ],
)
def test_get_latest_model(db_get_latest_model, model_id, expected_result):
    """
    Check, that function will return latest model.
    """
    actual_result = get_latest_model(db_get_latest_model, model_id)

    if actual_result is None:
        assert actual_result is expected_result
    else:
        actual_result = row_to_dict(actual_result)
        delete_date_field([actual_result], "created_at")
        assert actual_result == expected_result
