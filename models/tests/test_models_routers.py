import json
from unittest.mock import Mock, patch

import pytest
from fastapi.exceptions import HTTPException
from fastapi.testclient import TestClient

from src.db import Basement, Model, StatusEnum
from src.main import app
from src.routers import models_routers
from tests.override_app_dependency import TEST_HEADER, TEST_TENANTS
from tests.test_crud import GET_BASEMENT
from tests.utils import create_expected_models, delete_date_field, row_to_dict


@pytest.fixture(scope="function")
def client():
    client = TestClient(app)
    return client


@pytest.mark.integration
@pytest.mark.parametrize(
    ["number_of_models_in_db", "expected_result", "db_model"],
    [
        # model with provided id does not exist
        # it will be created
        # version should be 1
        # latest flag should be True
        # model in db should have
        # latest flag - True
        # version - 1
        (
            0,
            create_expected_models(
                latest=True,
                version=1,
                basement_id=GET_BASEMENT.id,
                categories=["category"],
                created_by="UUID",
                model_id="id",
                status=StatusEnum.READY,
                tenant=TEST_TENANTS[0],
                name="name",
            ),
            create_expected_models(
                latest=True,
                version=1,
                basement_id=GET_BASEMENT.id,
                categories=["category"],
                created_by="UUID",
                model_id="id",
                status=StatusEnum.READY,
                tenant=TEST_TENANTS[0],
                name="name",
            ),
        ),
        # model with provided id exists
        # new version with the same id will be created
        # version should be 2
        # latest flag should be True
        # first version of model in db should have
        # latest flag - False
        # version - 1
        (
            1,
            create_expected_models(
                latest=True,
                version=2,
                basement_id=GET_BASEMENT.id,
                categories=["category"],
                created_by="UUID",
                model_id="id",
                status=StatusEnum.READY,
                tenant=TEST_TENANTS[0],
                name="name",
            ),
            create_expected_models(
                latest=False,
                version=1,
                basement_id=GET_BASEMENT.id,
                categories=["category"],
                created_by="UUID",
                model_id="id",
                status=StatusEnum.READY,
                tenant=TEST_TENANTS[0],
                name="name",
            ),
        ),
    ],
)
def test_create_model(
    prepare_db_model,
    overrided_token_client,
    number_of_models_in_db,
    expected_result,
    db_model,
):
    """
    Check, that new model will be created correctly with already
    existing model in db and without it.
    """
    request_body = {
        "id": expected_result["id"],
        "name": expected_result["name"],
        "basement": expected_result["basement"],
        "categories": expected_result["categories"],
    }

    for i in range(number_of_models_in_db):
        overrided_token_client.post(
            "/models/create",
            json=request_body,
            headers=TEST_HEADER,
        )
    response = overrided_token_client.post(
        "/models/create",
        json=request_body,
        headers=TEST_HEADER,
    )

    actual_db_model = (
        prepare_db_model.query(Model)
        .filter(Model.id == request_body["id"])
        .order_by(Model.version)
        .first()
    )

    actual_db_model = row_to_dict(actual_db_model)
    delete_date_field([actual_db_model], "created_at")
    assert actual_db_model == db_model
    assert response.status_code == 201
    response = response.json()
    delete_date_field([response], "created_at")
    assert response == expected_result


@patch.object(models_routers.crud, "create_instance")
@patch.object(models_routers.crud, "is_id_existing")
def test_create_model_raises_401_without_token(exist, create, client):
    models_routers.get_db = Mock()
    data = {
        "id": "id",
        "name": "name",
        "basement": "basement",
        "categories": ["category"],
    }
    response = client.post("/models/create", data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail": "No authorization provided!"}
    exist.assert_not_called()
    create.assert_not_called()


@patch.object(models_routers.crud, "get_latest_model")
def test_get_model_by_id(get):
    get.return_value = "expected"
    assert models_routers.get_model_by_id("id", "session") == "expected"


@patch.object(models_routers.crud, "get_latest_model")
def test_get_model_by_id_withot_model(get):
    get.return_value = None
    with pytest.raises(HTTPException):
        assert models_routers.get_model_by_id("id", "session") == {
            "detail": "Not existing model"
        }


@patch.object(models_routers.crud, "delete_instance")
@patch.object(models_routers.crud, "get_latest_model")
def test_delete_model_by_id(get, delete, client):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    get.return_value = Mock(latest=False)
    response = client.delete("/models/delete", data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == {"msg": "Model was deleted"}


@patch.object(models_routers.crud, "delete_instance")
@patch.object(models_routers.crud, "get_latest_model")
def test_delete_model_by_id_calls_crud(get, delete):
    data = models_routers.schemas.ModelId(id="id")
    get.return_value = Mock(latest=False)
    models_routers.delete_model_by_id(data, "session")
    get.assert_called_once_with("session", "id")
    delete.assert_called_once_with("session", get.return_value)


@patch.object(models_routers.crud, "delete_instance")
@patch.object(models_routers.crud, "get_latest_model")
def test_delete_model_by_id_without_model(get, delete, client):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    get.return_value = None
    response = client.delete("/models/delete", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing model"}


@patch.object(models_routers.crud, "delete_instance")
@patch.object(models_routers.crud, "get_latest_model")
def test_delete_model_by_id_withot_model_calls_not_all_crud(get, delete):
    data = models_routers.schemas.ModelId(id="id")
    get.return_value = None
    with pytest.raises(HTTPException):
        models_routers.delete_model_by_id(data, "session")
    get.assert_called_once_with("session", "id")
    delete.assert_not_called()


@patch.object(models_routers.crud, "delete_instance")
@patch.object(models_routers.crud, "get_latest_model")
def test_delete_model_by_id_with_wrong_type(get, delete, client):
    data = {"id": [1]}
    models_routers.get_db = Mock()
    response = client.delete("/models/delete", data=json.dumps(data))
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


@patch.object(models_routers.crud, "get_latest_model")
def test_deploy_model_without_model(get, client):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    get.return_value = None
    response = client.post("/models/deploy", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing model"}


@patch.object(models_routers.utils, "deploy")
@patch.object(models_routers.crud, "get_latest_model")
def test_deploy_model_without_model_calls_only_crud(get, deploy):
    data = models_routers.schemas.ModelId(id="id")
    get.return_value = None
    with pytest.raises(HTTPException):
        models_routers.deploy_model(data, "session")
    get.assert_called_once_with("session", "id")
    deploy.assert_not_called()


@patch.object(models_routers.crud, "get_latest_model")
def test_deploy_model_with_wrong_type(get, client):
    data = {"id": [1]}
    models_routers.get_db = Mock()
    response = client.post("/models/deploy", data=json.dumps(data))
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


@patch.object(models_routers.crud, "modify_status")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_deploy_already_deployed_model_returns_409(
    get, is_deployed, modify, client
):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    query = models_routers.schemas.ModelId(id="id")
    get.return_value = query
    is_deployed.return_value = True
    response = client.post("/models/deploy", data=json.dumps(data))
    assert response.status_code == 409
    assert response.json() == {"detail": "Model id has already been deployed"}


@patch.object(models_routers.crud, "modify_status")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_deploy_already_deployed_model_modifies_status(
    get, is_deployed, modify
):
    data = models_routers.schemas.ModelId(id="id")
    models_routers.get_db = Mock()
    get.return_value = data
    is_deployed.return_value = True
    with pytest.raises(HTTPException):
        models_routers.deploy_model(data, "session")
    get.assert_called_once_with("session", "id")
    modify.assert_called_once_with("session", data, "ready", "deployed")


@patch.object(models_routers.utils, "deploy")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_deploy_model_in_positive_case(get, is_deployed, deploy, client):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    query = models_routers.schemas.ModelId(id="id")
    get.return_value = query
    is_deployed.return_value = False
    response = client.post("/models/deploy", data=json.dumps(data))
    assert response.status_code == 201
    assert response.json() == {"msg": "Model id is deploying"}


@patch.object(models_routers.utils, "deploy")
@patch.object(models_routers.crud, "modify_status")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_deploy_model_without_modifying_status(
    get, is_deployed, modify, deploy
):
    data = models_routers.schemas.ModelId(id="id")
    models_routers.get_db = Mock()
    get.return_value = data
    is_deployed.return_value = False
    models_routers.deploy_model(data, "session")
    get.assert_called_once_with("session", "id")
    modify.assert_not_called()
    deploy.assert_called_once_with("session", data)


@patch.object(models_routers.crud, "get_latest_model")
def test_undeploy_model_without_model(get, client):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    get.return_value = None
    response = client.delete("/models/undeploy", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing model"}


@patch.object(models_routers.utils, "undeploy")
@patch.object(models_routers.crud, "get_latest_model")
def test_undeploy_model_without_model_calls_only_crud(get, undeploy):
    data = models_routers.schemas.ModelId(id="id")
    get.return_value = None
    with pytest.raises(HTTPException):
        models_routers.undeploy_model(data, "session")
    get.assert_called_once_with("session", "id")
    undeploy.assert_not_called()


@patch.object(models_routers.utils, "undeploy")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_undeploy_model_in_positive_case(get, is_deployed, undeploy, client):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    query = models_routers.schemas.ModelId(id="id")
    get.return_value = query
    is_deployed.return_value = True
    undeploy.return_value = True
    response = client.delete("/models/undeploy", data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == {"msg": "Model id is undeployed"}


@patch.object(models_routers.utils, "undeploy")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_undeploy_model_in_negative_case(get, is_deployed, undeploy, client):
    data = {"id": "id"}
    models_routers.get_db = Mock()
    query = models_routers.schemas.ModelId(id="id")
    get.return_value = query
    is_deployed.return_value = True
    undeploy.return_value = False
    response = client.delete("/models/undeploy", data=json.dumps(data))
    assert response.status_code == 409
    assert response.json() == {"detail": "Failed to undeploy model id"}


@patch.object(models_routers.utils, "undeploy")
@patch.object(models_routers.crud, "modify_status")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_undeploy_already_undeployed_model_modifies_status(
    get, is_deployed, modify, undeploy
):
    data = models_routers.schemas.ModelId(id="id")
    models_routers.get_db = Mock()
    get.return_value = data
    is_deployed.return_value = False
    models_routers.undeploy_model(data, "session")
    get.assert_called_once_with("session", "id")
    modify.assert_called_once_with("session", data, "deployed", "ready")
    undeploy.assert_not_called()


@patch.object(models_routers.utils, "undeploy")
@patch.object(models_routers.crud, "modify_status")
@patch.object(models_routers.utils, "is_model_deployed")
@patch.object(models_routers.crud, "get_latest_model")
def test_undeploy_model_calls_undeploying_function(
    get, is_deployed, modify, undeploy
):
    data = models_routers.schemas.ModelId(id="id")
    models_routers.get_db = Mock()
    get.return_value = data
    is_deployed.return_value = True
    models_routers.undeploy_model(data, "session")
    get.assert_called_once_with("session", "id")
    modify.assert_not_called()
    undeploy.assert_called_once_with("session", data)


@patch.object(models_routers.crud, "get_latest_model")
def test_update_not_existing_model_raises_404(get, client):
    data = {
        "id": "id",
        "name": "name",
        "basement": "basement",
        "categories": ["category"],
    }
    get.return_value = None
    response = client.put("/models/update", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing model"}


def test_update_model_with_wrong_data_raises_422(client):
    data = {
        "id": "id",
        "name": [1],
        "basement": "basement",
        "categories": ["category"],
    }
    response = client.put("/models/update", data=json.dumps(data))
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


@patch.object(models_routers.crud, "modify_instance")
@patch.object(models_routers.crud, "is_id_existing")
@patch.object(models_routers.crud, "get_latest_model")
def test_update_model_in_positive_case(_get, exist, modify, client):
    data = {
        "id": "id",
        "name": "name",
        "basement": "basement",
        "categories": ["category"],
        "training_id": 4,
    }
    modify.return_value = {"model": "model"}
    exist.return_value = True
    response = client.put("/models/update", data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == {"model": "model"}


@patch.object(models_routers.crud, "modify_instance")
@patch.object(models_routers.crud, "is_id_existing")
@patch.object(models_routers.crud, "get_latest_model")
def test_update_model_in_positive_case_calls_crud(get, exist, modify):
    data = models_routers.schemas.ModelWithId(
        id="id", name="name", basement="basement", categories=["categories"]
    )
    get.return_value = "model"
    exist.return_value = True
    models_routers.update_model(data, "session")
    get.assert_called_once_with("session", "id")
    exist.assert_called_once_with("session", Basement, "basement")
    modify.assert_called_once_with("session", "model", data)


@patch.object(models_routers.crud, "is_id_existing")
@patch.object(models_routers.crud, "get_latest_model")
def test_update_model_without_basement_raises_404(get, exist, client):
    data = {
        "id": "id",
        "name": "name",
        "basement": "basement",
        "categories": ["category"],
    }
    get.return_value = "model"
    exist.return_value = False
    response = client.put("/models/update", data=json.dumps(data))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing basement"}
