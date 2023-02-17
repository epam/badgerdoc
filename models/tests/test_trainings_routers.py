import json
from unittest.mock import Mock, patch

import pytest
from fastapi.exceptions import HTTPException
from fastapi.testclient import TestClient

from models.db import Basement, Training
from models.main import app
from models.routers import training_routers

from .override_app_dependency import TEST_HEADER


@pytest.fixture(scope="function")
def client():
    client = TestClient(app)
    return client


@patch.object(training_routers.crud, "create_instance")
@patch.object(training_routers.crud, "is_id_existing")
def test_create_training_raises_401_without_token(exist, create, client):
    training_routers.get_db = Mock()
    data = {
        "id": "id",
        "name": "name",
        "files_ids": [1],
        "datasets_ids": [1],
        "basement": "basement",
        "epochs_count": 12,
    }
    response = client.post("/trainings/create", data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail": "No authorization provided!"}
    exist.assert_not_called()
    create.assert_not_called()


@patch.object(training_routers.crud, "get_instance")
@patch.object(training_routers.crud, "create_instance")
@patch.object(training_routers.crud, "is_id_existing")
def test_create_training_in_positive_case(exist, create, _get):
    data = training_routers.schemas.TrainingBase(
        name="name",
        jobs=[1],
        basement="basement",
        epochs_count=12,
    )
    exist.return_value = True
    create.return_value = {"id": "id"}
    token = Mock()
    token.user_id.return_value = "token"
    assert training_routers.create_new_training(data, "session", token, "tenant") == {
        "id": "id"
    }
    exist.assert_called_once_with("session", Basement, "basement")
    create.assert_called_once_with("session", Training, data, token.user_id, "tenant")


@patch.object(training_routers.crud, "create_instance")
@patch.object(training_routers.crud, "is_id_existing")
def test_create_training_raises_error_without_basement(exist, create):
    data = training_routers.schemas.TrainingBase(
        id="id",
        name="name",
        jobs=[1],
        basement="basement",
        epochs_count=12,
    )
    exist.return_value = False
    token = Mock()
    token.user_id.return_value = "token"
    with pytest.raises(HTTPException):
        response = training_routers.create_new_training(
            data, "session", token, "tenant"
        )
        assert response == {"detail": "Not existing basement"}
    exist.assert_called_once_with("session", Basement, "basement")
    create.assert_not_called()


@patch.object(training_routers.crud, "get_instance")
def test_get_training_by_id(get):
    get.return_value = "expected"
    assert training_routers.get_training_by_id(1, "session") == "expected"


@patch.object(training_routers.crud, "get_instance")
def test_get_training_by_id_withot_training(get):
    get.return_value = None
    with pytest.raises(HTTPException):
        assert training_routers.get_training_by_id(1, "session") == {
            "detail": "Not existing training"
        }


@patch.object(training_routers.crud, "delete_instance")
@patch.object(training_routers.crud, "get_instance")
@patch("models.routers.training_routers.get_minio_resource", Mock())
def test_delete_training_by_id(get, delete, client):
    data = {"id": 1}
    training_routers.get_db = Mock()
    get.return_value = Mock()
    response = client.delete(
        "/trainings/delete", data=json.dumps(data), headers=TEST_HEADER
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Training was deleted"}


@patch.object(training_routers.crud, "delete_instance")
@patch.object(training_routers.crud, "get_instance")
@patch("models.routers.training_routers.get_minio_resource", Mock())
def test_delete_training_by_id_calls_crud(get, delete):
    data = training_routers.schemas.TrainingDelete(id=1)
    db_entity = Mock()
    get.return_value = db_entity
    training_routers.delete_training_by_id(data, "session")
    get.assert_called_once_with("session", Training, 1)
    delete.assert_called_once_with("session", db_entity)


@patch.object(training_routers.crud, "delete_instance")
@patch.object(training_routers.crud, "get_instance")
def test_delete_training_by_id_without_training(get, delete, client):
    data = {"id": 1}
    training_routers.get_db = Mock()
    get.return_value = None
    response = client.delete(
        "/trainings/delete", data=json.dumps(data), headers=TEST_HEADER
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing training"}


@patch.object(training_routers.crud, "delete_instance")
@patch.object(training_routers.crud, "get_instance")
def test_delete_training_by_id_withot_training_calls_not_all_crud(get, delete):
    data = training_routers.schemas.TrainingDelete(id=1)
    get.return_value = None
    with pytest.raises(HTTPException):
        training_routers.delete_training_by_id(data, "session")
    get.assert_called_once_with("session", Training, 1)
    delete.assert_not_called()


@patch.object(training_routers.crud, "delete_instance")
@patch.object(training_routers.crud, "get_instance")
def test_delete_training_by_id_with_wrong_type(get, delete, client):
    data = {"id": "id"}
    training_routers.get_db = Mock()
    response = client.delete(
        "/trainings/delete", data=json.dumps(data), headers=TEST_HEADER
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "id"],
                "msg": "value is not a valid integer",
                "type": "type_error.integer",
            }
        ]
    }


@patch.object(training_routers.crud, "get_instance")
def test_update_not_existing_training_raises_404(get, client):
    data = {
        "id": 1,
        "name": "name",
        "jobs": [1],
        "basement": "basement",
        "epochs_count": 1,
    }
    get.return_value = None
    response = client.put("/trainings/update", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing training"}


def test_update_training_with_wrong_data_raises_422(client):
    data = {
        "id": "id",
        "name": "name",
        "jobs": [1],
        "basement": "basement",
        "epochs_count": 1,
    }
    response = client.put("/trainings/update", data=json.dumps(data))
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "id"],
                "msg": "value is not a valid integer",
                "type": "type_error.integer",
            }
        ]
    }


@patch.object(training_routers.crud, "modify_instance")
@patch.object(training_routers.crud, "is_id_existing")
@patch.object(training_routers.crud, "get_instance")
def test_update_training_in_positive_case(_get, exist, modify, client):
    data = {
        "id": 1,
        "name": "name",
        "jobs": [1],
        "basement": "basement",
        "epochs_count": 1,
    }
    modify.return_value = {"training": "training"}
    exist.return_value = True
    response = client.put("/trainings/update", data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == {"training": "training"}


@patch.object(training_routers.crud, "modify_instance")
@patch.object(training_routers.crud, "is_id_existing")
@patch.object(training_routers.crud, "get_instance")
def test_update_training_in_positive_case_calls_crud(get, exist, modify):
    data = training_routers.schemas.TrainingUpdate(
        id=1,
        name="name",
        jobs=[1],
        basement="basement",
        epochs_count=12,
    )
    get.return_value = "training"
    exist.return_value = True
    training_routers.update_training(data, "session")
    get.assert_called_once_with("session", Training, 1)
    exist.assert_called_once_with("session", Basement, "basement")
    modify.assert_called_once_with("session", "training", data)


@patch.object(training_routers.crud, "is_id_existing")
@patch.object(training_routers.crud, "get_instance")
def test_update_training_without_basement_raises_404(get, exist, client):
    data = {
        "id": 1,
        "name": "name",
        "jobs": [1],
        "basement": "basement",
        "epochs_count": 1,
    }
    get.return_value = "training"
    exist.return_value = False
    response = client.put("/trainings/update", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing basement"}
