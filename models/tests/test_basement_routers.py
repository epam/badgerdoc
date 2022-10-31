import json
from unittest.mock import Mock, patch

import pytest
from fastapi.exceptions import HTTPException
from fastapi.testclient import TestClient

from src.db import Basement
from src.main import app
from src.routers import basements_routers
from tests.test_utils import TEST_LIMITS


@pytest.fixture(scope="function")
def client():
    client = TestClient(app)
    return client


@patch.object(basements_routers.crud, "create_instance")
@patch.object(basements_routers.crud, "is_id_existing")
def test_create_basement(exist, create):
    data = basements_routers.schemas.BasementBase(
        id="id", name="name", gpu_support=False, limits=TEST_LIMITS
    )
    exist.return_value = False
    create.return_value = {"msg": "expected"}
    token = Mock()
    token.user_id.return_value = "token"
    assert basements_routers.create_new_basement(
        data, "session", token, "tenant"
    ) == {"msg": "expected"}
    exist.assert_called_once_with("session", Basement, "id")
    create.assert_called_once_with(
        "session", Basement, data, token.user_id, "tenant"
    )


@patch.object(basements_routers.crud, "create_instance")
@patch.object(basements_routers.crud, "is_id_existing")
def test_create_basement_raises_error_when_basement_exists(exist, create):
    data = basements_routers.schemas.BasementBase(
        id="id", name="name", gpu_support=False, limits=TEST_LIMITS
    )
    exist.return_value = True
    token = Mock()
    token.user_id.return_value = "token"
    with pytest.raises(HTTPException):
        response = basements_routers.create_new_basement(
            data, "session", token, "tenant"
        )
        assert response == {"detail": "Id has to be unique name"}

    exist.assert_called_once_with("session", Basement, "id")
    create.assert_not_called()


@patch.object(basements_routers.crud, "create_instance")
@patch.object(basements_routers.crud, "is_id_existing")
def test_create_basement_raises_401_without_token(exist, create, client):
    data = {"id": "id", "name": "name", "gpu_support": False}
    response = client.post("/basements/create", data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail": "No authorization provided!"}
    exist.assert_not_called()
    create.assert_not_called()


@patch.object(basements_routers.crud, "get_instance")
def test_get_basemnet_by_id(get):
    get.return_value = "expected"
    assert basements_routers.get_basement_by_id("id", "session") == "expected"


@patch.object(basements_routers.crud, "get_instance")
def test_get_basement_by_id_withot_basement(get):
    get.return_value = None
    with pytest.raises(HTTPException):
        assert basements_routers.get_basement_by_id("id", "session") == {
            "detail": "Not existing basement"
        }


@patch.object(basements_routers.crud, "delete_instance")
@patch.object(basements_routers.crud, "get_instance")
def test_delete_basement_by_id(delete, get, client, monkeypatch):
    monkeypatch.setattr(
        "src.routers.basements_routers.get_minio_resource", Mock()
    )
    data = {"id": "id"}
    get.return_value = "expected"
    response = client.delete("/basements/delete", data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == {"msg": "Basement was deleted"}


@patch.object(basements_routers.crud, "delete_instance")
@patch.object(basements_routers.crud, "get_instance")
def test_delete_basement_by_id_calls_crud(delete, get, monkeypatch):
    monkeypatch.setattr(
        "src.routers.basements_routers.get_minio_resource", Mock()
    )
    data = basements_routers.schemas.BasementDelete(id="id")
    get.return_value = "expected"
    basements_routers.delete_basement_by_id(data, "session")
    delete.assert_called_once_with("session", Basement, "id")


@patch.object(basements_routers.crud, "delete_instance")
@patch.object(basements_routers.crud, "get_instance")
def test_delete_basement_by_id_without_basement(get, delete, client):
    data = {"id": "id"}
    get.return_value = None
    response = client.delete("/basements/delete", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing basement"}


@patch.object(basements_routers.crud, "delete_instance")
@patch.object(basements_routers.crud, "get_instance")
def test_delete_basement_by_id_withot_basement_calls_not_all_crud(get, delete):
    data = basements_routers.schemas.BasementDelete(id="id")
    get.return_value = None
    with pytest.raises(HTTPException):
        basements_routers.delete_basement_by_id(data, "session")
    get.assert_called_once_with("session", Basement, "id")
    delete.assert_not_called()


@patch.object(basements_routers.crud, "delete_instance")
@patch.object(basements_routers.crud, "get_instance")
def test_delete_basement_by_id_with_wrong_type(get, delete, client):
    data = {"id": [1]}
    response = client.delete("/basements/delete", data=json.dumps(data))
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "id"],
                "msg": "str type expected",
                "type": "type_error.str",
            }
        ]
    }


@patch.object(basements_routers.crud, "get_instance")
def test_update_not_existing_basement_raises_404(get, client):
    data = {
        "id": "id",
        "name": "name",
        "gpu_support": False,
        "limits": TEST_LIMITS,
    }
    get.return_value = None
    response = client.put("/basements/update", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing basement"}


def test_update_basement_with_wrong_data_raises_422(client):
    data = {
        "id": "id",
        "name": [1],
        "gpu_support": False,
        "limits": TEST_LIMITS,
    }
    response = client.put("/basements/update", data=json.dumps(data))
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "name"],
                "msg": "str type expected",
                "type": "type_error.str",
            }
        ]
    }


@patch.object(basements_routers.crud, "modify_instance")
@patch.object(basements_routers.crud, "get_instance")
def test_update_basement_in_positive_case(_get, modify, client):
    data = {
        "id": "id",
        "name": "name",
        "gpu_support": False,
        "limits": TEST_LIMITS,
    }
    modify.return_value = {"basement": "basement"}
    response = client.put("/basements/update", data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == {"basement": "basement"}


@patch.object(basements_routers.crud, "modify_instance")
@patch.object(basements_routers.crud, "get_instance")
def test_update_basement_in_positive_case_calls_crud(get, modify):
    data = basements_routers.schemas.BasementBase(
        id="id", name="name", gpu_support=False, limits=TEST_LIMITS
    )
    get.return_value = "basement"
    basements_routers.update_basement(data, "session")
    get.assert_called_once_with("session", Basement, "id")
    modify.assert_called_once_with("session", "basement", data)
