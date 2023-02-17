from unittest.mock import Mock, patch

import pytest
from kubernetes.client.exceptions import ApiException

from models.routers import deployed_models_routers
from models.schemas import DeployedModelPod


def test_get_deployed_model_list_returns_list_of_models(client):
    deployed_models_routers.config = Mock()
    api = Mock()
    deployed_models_routers.client.CustomObjectsApi = Mock(return_value=api)
    deployed_models_routers.MODELS_NAMESPACE = "namespace"
    expected = {
        "items": [
            {
                "metadata": {
                    "creationTimestamp": "2015-02-10T13:00:00Z",
                    "name": "name",
                },
                "status": {"conditions": [{"status": "status"}], "url": "url"},
            }
        ]
    }
    api.list_namespaced_custom_object = Mock(return_value=expected)
    response = client.get("deployed_models/search")
    api.list_namespaced_custom_object.assert_called_once_with(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace="namespace",
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "datetime_creation": "2015-02-10 13:00:00",
            "status": "status",
            "name": "name",
            "url": "url",
        }
    ]


def test_get_deployed_model_by_name(client):
    deployed_models_routers.config = Mock()
    api = Mock()
    deployed_models_routers.client.CustomObjectsApi = Mock(return_value=api)
    expected = {
        "metadata": {
            "creationTimestamp": "2015-02-10T13:00:00Z",
            "name": "name",
            "generation": 1,
            "namespace": "namespace",
            "resourceVersion": "resourceVersion",
            "uid": "uid",
        },
        "status": {"conditions": [{"status": "status"}], "url": "url"},
        "apiVersion": "apiVersion",
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "image": "image",
                            "name": "name",
                            "ports": [{"ports": "ports"}],
                        }
                    ]
                }
            }
        },
    }
    api.get_namespaced_custom_object = Mock(return_value=expected)
    deployed_models_routers.MODELS_NAMESPACE = "namespace"
    response = client.get("deployed_models/name")
    assert response.status_code == 200
    api.get_namespaced_custom_object.assert_called_once_with(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace="namespace",
        name="name",
    )
    assert response.json() == {
        "apiVersion": "apiVersion",
        "datetime_creation": "2015-02-10 13:00:00",
        "model_id": 1,
        "model_name": "name",
        "status": "status",
        "reason": None,
        "message": None,
        "namespace": "namespace",
        "resourceVersion": "resourceVersion",
        "uuid": "uid",
        "image": "image",
        "container_name": "name",
        "ports": [{"ports": "ports"}],
        "url": "url",
    }


def test_get_deployed_model_by_name_when_model_does_not_exist(client):
    deployed_models_routers.config = Mock()
    api = Mock()
    deployed_models_routers.client.CustomObjectsApi = Mock(return_value=api)
    api.get_namespaced_custom_object.side_effect = ApiException(status=404)
    response = client.get("deployed_models/name")
    api.get_namespaced_custom_object.assert_called_once_with(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace=deployed_models_routers.MODELS_NAMESPACE,
        name="name",
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing model"}


def test_get_deployed_model_by_name_with_raising_error(client):
    deployed_models_routers.config = Mock()
    api = Mock()
    deployed_models_routers.client.CustomObjectsApi = Mock(return_value=api)
    api.get_namespaced_custom_object.side_effect = ApiException
    with pytest.raises(ApiException):
        client.get("deployed_models/name")
    api.get_namespaced_custom_object.assert_called_once_with(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace=deployed_models_routers.MODELS_NAMESPACE,
        name="name",
    )


@patch.object(deployed_models_routers.utils, "get_pods")
def test_get_deployed_model_pods(get):
    deployed_models_routers.config = Mock()
    api = Mock()
    deployed_models_routers.client.CustomObjectsApi = Mock(return_value=api)
    expected = [
        DeployedModelPod(
            name="name",
            status="Terminating",
            failures=[],
            start_time="1",
            logs="logs",
        )
    ]
    get.return_value = expected
    assert deployed_models_routers.get_deployed_model_pods("name") == expected
    api.get_namespaced_custom_object.assert_called_once_with(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace=deployed_models_routers.MODELS_NAMESPACE,
        name="name",
    )


def test_get_deployed_model_pods_raises_error():
    deployed_models_routers.config = Mock()
    api = Mock()
    deployed_models_routers.client.CustomObjectsApi = Mock(return_value=api)
    api.get_namespaced_custom_object.side_effect = ApiException
    with pytest.raises(ApiException):
        deployed_models_routers.get_deployed_model_pods("name")
    api.get_namespaced_custom_object.assert_called_once_with(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace=deployed_models_routers.MODELS_NAMESPACE,
        name="name",
    )


def test_get_deployed_model_pods_when_model_does_not_exist(client):
    deployed_models_routers.config = Mock()
    api = Mock()
    deployed_models_routers.client.CustomObjectsApi = Mock(return_value=api)
    api.get_namespaced_custom_object.side_effect = ApiException(status=404)
    response = client.get("deployed_models/name")
    api.get_namespaced_custom_object.assert_called_once_with(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace=deployed_models_routers.MODELS_NAMESPACE,
        name="name",
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Not existing model"}
