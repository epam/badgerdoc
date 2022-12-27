import json
import time
from collections import namedtuple
from unittest.mock import Mock, patch

import pytest
import requests
from botocore.exceptions import ClientError
from kubernetes.client.rest import ApiException

from src import utils
from src.constants import MINIO_HOST
from src.errors import NoSuchTenant
from src.schemas import (
    BasementBase,
    DeployedModelPod,
    MinioHTTPMethod,
    MinioPath,
    Model,
)

TEST_TENANT = "test"
TEST_LIMITS = {
    "pod_cpu": "1000m",
    "pod_memory": "2Gi",
    "concurrency_limit": 1,
}


def test_minio_no_such_bucket_error_handling(moto_minio, monkeypatch):
    """Tests that attempt to get resource for bucket of not existing tenant
    will raise "NoSuchTenant" exception with appropriate message.
    """
    wrong_tenant = "wrong_tenant"
    error_message = f"Bucket {wrong_tenant} does not exist"
    monkeypatch.setattr(
        "src.utils.boto3.resource",
        Mock(return_value=moto_minio),
    )
    with pytest.raises(utils.NoSuchTenant, match=error_message):
        utils.get_minio_resource("wrong_tenant")


@pytest.mark.parametrize(
    ["save_object_minio", "request_key", "expected_text", "expected_code"],
    [
        (
            [{"file_id": 1}, "file_1.json"],
            "file_1.json",
            '{"file_id": 1}',
            200,
        ),  # try to get Object with existing key in minio and generated URL
        (
            [{"file_id": 1}, "file_1.json"],
            "file_2.json",
            "key does not exist",
            404,
        ),  # try to get not-existing Object in minio with generated URL
    ],
    indirect=["save_object_minio"],
)
def test_get_object_via_presigned_url(
    save_object_minio,
    request_key,
    expected_text,
    monkeypatch,
    expected_code,
):
    """Tests possibility to GET object via generated presigned URL."""
    monkeypatch.setattr(
        "src.utils.get_minio_resource",
        Mock(return_value=save_object_minio),
    )
    presigned_url = utils.generate_presigned_url(
        http_method=MinioHTTPMethod.get_object,
        bucket_name=TEST_TENANT,
        key=request_key,
        expiration=5,
    )
    assert presigned_url
    minio_response = requests.get(presigned_url)
    assert minio_response.status_code == expected_code
    assert expected_text in minio_response.text


@pytest.mark.parametrize(
    ["minio_method", "key", "expiration"],
    [
        (MinioHTTPMethod.get_object, "file_1", 5),
        (MinioHTTPMethod.put_object, "file_2", 10),
    ],
)
def test_generate_presigned_url(
    moto_minio,
    monkeypatch,
    minio_method,
    key,
    expiration,
):
    """Checks that "utils.generate_presigned_url" function returns presigned
    URL with correct key, expiration time and signature-generating algorithm.
    """
    monkeypatch.setattr(
        "src.utils.get_minio_resource",
        Mock(return_value=moto_minio),
    )
    presigned_url = utils.generate_presigned_url(
        http_method=minio_method,
        bucket_name=TEST_TENANT,
        key=key,
        expiration=expiration,
    )
    assert key in presigned_url
    assert f"X-Amz-Expires={expiration}" in presigned_url
    assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in presigned_url


@patch("src.utils.MINIO_PUBLIC_HOST", MINIO_HOST)
@pytest.mark.integration
def test_expired_presigned_url(create_minio_bucket):
    """Tests that http_method actions for minio Object won't be applicable
    when presigned URL expires. Note: moto doesn't support expiration check
    of presigned links, that's why this could be tested only in case of
    integration with minio instance.
    """
    presigned_url = utils.generate_presigned_url(
        http_method=MinioHTTPMethod.get_object,
        bucket_name=TEST_TENANT,
        key="file_1.json",
        expiration=1,
    )
    assert presigned_url
    time.sleep(2)
    minio_response = requests.get(presigned_url)
    assert minio_response.status_code == 403
    assert "Request has expired" in minio_response.text


def test_generate_presigned_url_error(moto_minio, monkeypatch):
    """Checks that "generate_presigned_url" function returns None in cases
    of boto3 errors.
    """
    monkeypatch.setattr(
        "src.utils.get_minio_resource",
        Mock(return_value=moto_minio),
    )
    presigned_url = utils.generate_presigned_url(
        http_method="some_wrong_method",
        bucket_name=TEST_TENANT,
        key="file_1.json",
        expiration=1,
    )
    assert not presigned_url


def test_put_object_via_presigned_url(moto_minio, monkeypatch):
    """Tests possibility to PUT object in minio via generated presigned URL."""
    key = "test_file.json"
    test_data = {"file_id": 1}
    monkeypatch.setattr(
        "src.utils.get_minio_resource",
        Mock(return_value=moto_minio),
    )
    presigned_url = utils.generate_presigned_url(
        http_method=MinioHTTPMethod.put_object,
        bucket_name=TEST_TENANT,
        key=key,
        expiration=5,
    )
    assert presigned_url
    minio_response = requests.put(presigned_url, json=test_data)
    assert minio_response.status_code == 200
    minio_object = (
        moto_minio.Object(TEST_TENANT, key)
        .get()["Body"]
        .read()
        .decode("utf-8")
    )
    assert json.loads(minio_object) == test_data


def test_is_mapping_deployed_returns_true():
    api = Mock()
    api.get_namespaced_custom_object.return_value = True
    assert utils.is_mapping_deployed("name", api) is True


def test_is_mapping_deployed_returns_false_without_mapping():
    api = Mock()
    api.get_namespaced_custom_object.side_effect = ApiException(status=404)
    assert utils.is_mapping_deployed("name", api) is False


def test_is_mapping_deployed_raises_error():
    api = Mock()
    api.get_namespaced_custom_object = Mock(side_effect=ApiException)
    with pytest.raises(ApiException):
        utils.is_mapping_deployed("name", api)


def test_is_model_deployed_returns_true():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    api.get_namespaced_custom_object.return_value = True
    assert utils.is_model_deployed("name") is True


def test_is_model_deployed_returns_false_without_model():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    api.get_namespaced_custom_object.side_effect = ApiException(status=404)
    assert utils.is_model_deployed("name") is False


def test_is_model_deployed_raises_error():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    api.get_namespaced_custom_object = Mock(side_effect=ApiException)
    with pytest.raises(ApiException):
        utils.is_model_deployed("name")


def test_delete_mapping_calls_api_and_returns_none():
    api = Mock()
    utils.MODELS_NAMESPACE = "namespace"
    assert utils.delete_mapping("name", api) is None
    api.delete_namespaced_custom_object.assert_called_once_with(
        "getambassador.io", "v2", "namespace", "mappings", "name"
    )


def test_delete_ksvc_calls_api_and_returns_true():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    utils.MODELS_NAMESPACE = "namespace"
    utils.is_mapping_deployed = Mock(return_value=True)
    utils.delete_mapping = Mock()
    assert utils.delete_ksvc("name") is True
    api.delete_namespaced_custom_object.assert_called_once_with(
        "serving.knative.dev", "v1", "namespace", "services", "name"
    )
    utils.delete_mapping.assert_called_once_with("name", api)


def test_delete_ksvc_doe_not_call_delete_mapping_without_mapping():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    utils.MODELS_NAMESPACE = "namespace"
    utils.is_mapping_deployed = Mock(return_value=False)
    utils.delete_mapping = Mock()
    assert utils.delete_ksvc("name") is True
    api.delete_namespaced_custom_object.assert_called_once_with(
        "serving.knative.dev", "v1", "namespace", "services", "name"
    )
    utils.delete_mapping.assert_not_called()


def test_delete_ksvc_returns_false_with_error():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    utils.MODELS_NAMESPACE = "namespace"
    utils.is_mapping_deployed = Mock()
    utils.delete_mapping = Mock()
    api.delete_namespaced_custom_object.side_effect = ApiException
    assert utils.delete_ksvc("name") is False
    api.delete_namespaced_custom_object.assert_called_once_with(
        "serving.knative.dev", "v1", "namespace", "services", "name"
    )


def test_assert_create_mapping_calls_api_and_returns_none():
    api = Mock()
    assert utils.create_mapping("name", api) is None
    api.create_namespaced_custom_object.assert_called_once()


def test_create_ksvc_calls_api_and_create_mapping_without_mapping():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    utils.is_mapping_deployed = Mock(return_value=False)
    utils.create_mapping = Mock()
    pth = {"bucket": "bucket", "file": "file"}
    data = (
        "name",
        "image",
        "device",
        pth,
        pth,
        "pod_cpu_limit",
        "pod_memory_limit",
        "concurrency_limit",
    )
    assert utils.create_ksvc(*data) is None
    utils.create_mapping.assert_called_once_with("name", api)
    api.create_namespaced_custom_object.assert_called_once()


def test_create_ksvc_does_not_call_create_mapping_with_mapping():
    utils.config = Mock()
    api = Mock()
    utils.client.CustomObjectsApi = Mock(return_value=api)
    utils.is_mapping_deployed = Mock(return_value=True)
    utils.create_mapping = Mock()
    pth = {"bucket": "bucket", "file": "file"}
    data = (
        "name",
        "image",
        "device",
        pth,
        pth,
        "pod_cpu_limit",
        "pod_memory_limit",
        "concurrency_limit",
    )
    assert utils.create_ksvc(*data) is None
    utils.create_mapping.assert_not_called()
    api.create_namespaced_custom_object.assert_called_once()


def test_deploy_calls_create_ksvc_and_changes_model_status():
    session = Mock()
    pth = MinioPath(bucket="bucket", file="file")
    model = Model(
        id="id",
        name="name",
        basement="basement",
        data_path=pth,
        configuration_path=pth,
        categories=["category"],
        status="ready",
        created_by="author",
        created_at="2021-11-09T17:09:43.101004",
        tenant="tenant",
        latest=True,
        version=1,
    )
    basement = BasementBase(id="id", name="name", limits={}, gpu_support=False)
    basement.limits = TEST_LIMITS
    session.query.return_value.get.return_value = basement
    utils.create_ksvc = Mock()
    assert utils.deploy(session, model) is None
    utils.create_ksvc.assert_called_once_with(
        "id", "basement", "cpu", pth, pth, "1000m", "2Gi", 1
    )
    session.commit.assert_called_once()
    assert model.status == "deployed"


def test_deploy_sets_default_value_for_path_without_path():
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
        latest=True,
        version=1,
    )
    basement = BasementBase(id="id", name="name", gpu_support=False, limits={})
    basement.limits = TEST_LIMITS
    session.query.return_value.get.return_value = basement
    utils.create_ksvc = Mock()
    default = {"bucket": "", "file": ""}
    assert utils.deploy(session, model) is None
    utils.create_ksvc.assert_called_once_with(
        "id", "basement", "cpu", default, default, "1000m", "2Gi", 1
    )


def test_deploy_sets_device_gpu_if_basement_gpu_support_is_true():
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
        latest=True,
        version=1,
    )
    basement = BasementBase(id="id", name="name", gpu_support=False, limits={})
    basement.limits = TEST_LIMITS
    session.query.return_value.get.return_value = basement
    utils.create_ksvc = Mock()
    default = {"bucket": "", "file": ""}
    assert utils.deploy(session, model) is None
    utils.create_ksvc.assert_called_once_with(
        "id", "basement", "cpu", default, default, "1000m", "2Gi", 1
    )


def test_undeploy_returns_true_and_sets_status_to_ready():
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
        latest=True,
        version=1,
    )
    utils.delete_ksvc = Mock(return_value=True)
    assert utils.undeploy(session, model) is True
    assert model.status == "ready"
    session.commit.assert_called_once()
    utils.delete_ksvc.assert_called_once_with("id")


def test_undeploy_returns_false_for_any_error_and_not_modify_status_to_ready():
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
        latest=True,
        version=1,
    )
    utils.delete_ksvc = Mock(return_value=False)
    assert utils.undeploy(session, model) is False
    assert model.status == "deployed"
    session.commit.assert_not_called()
    utils.delete_ksvc.assert_called_once_with("id")


def test_get_pods_with_terminating_status():
    api = Mock()
    utils.client = Mock()
    utils.client.CoreV1Api.return_value = api
    Pods = namedtuple("Pods", {"items"})
    Metadata = namedtuple(
        "Metadata", ("deletion_timestamp", "name", "namespace")
    )
    Status = namedtuple("Status", ("start_time", "container_statuses"))
    Container = namedtuple("Container", ("name"))
    container = Container("name")
    Pod = namedtuple("Pod", ("metadata", "status"))
    api.read_namespaced_pod_log.return_value = "logs"
    metadata = Metadata(True, "name", "space")
    status = Status(1, [container])
    pod = Pod(metadata, status)
    pods = Pods([pod])
    utils.CONTAINER_NAME = "another name"
    api.list_namespaced_pod.return_value = pods
    assert utils.get_pods("name") == [
        DeployedModelPod(
            name="name",
            status="Terminating",
            failures=[],
            start_time="1",
            logs="logs",
        )
    ]


def test_get_pods_with_running_status():
    api = Mock()
    utils.client = Mock()
    utils.client.CoreV1Api.return_value = api
    Pods = namedtuple("Pods", {"items"})
    Metadata = namedtuple(
        "Metadata", ("deletion_timestamp", "name", "namespace")
    )
    Status = namedtuple(
        "Status", ("start_time", "container_statuses", "phase")
    )
    Pod = namedtuple("Pod", ("metadata", "status"))
    Container = namedtuple("Container", ("name"))
    container = Container("name")
    api.read_namespaced_pod_log.return_value = "logs"
    metadata = Metadata(False, "name", "space")
    status = Status(1, [container], "Running")
    pod = Pod(metadata, status)
    pods = Pods([pod])
    utils.CONTAINER_NAME = "another name"
    api.list_namespaced_pod.return_value = pods
    assert utils.get_pods("name") == [
        DeployedModelPod(
            name="name",
            status="Running",
            failures=[],
            start_time="1",
            logs="logs",
        )
    ]


def test_get_minio_object_wrong_tenant(monkeypatch, moto_minio) -> None:
    """Tests that providing tenant with not existing bucket will raise
    'NoSuchTenant' exception with 'Bucket for tenant does not exist' message.
    """
    monkeypatch.setattr(
        "src.utils.boto3.resource",
        Mock(return_value=moto_minio),
    )
    wrong_tenant = "wrong_tenant"
    with pytest.raises(
        NoSuchTenant, match=f"Bucket {wrong_tenant} does not exist"
    ):
        utils.get_minio_object(wrong_tenant, "file/file.txt")


@pytest.mark.parametrize(
    "save_object_minio", [({"file_id": 1}, "file_1.json")], indirect=True
)
def test_get_minio_object_wrong_key(monkeypatch, save_object_minio) -> None:
    """Tests that providing no existing key will raise NoSuchKey exception with
    'The specified key does not exist' in error message.
    """
    monkeypatch.setattr(
        "src.utils.boto3.resource",
        Mock(return_value=save_object_minio),
    )
    with pytest.raises(ClientError, match=r"The specified key does not exist"):
        utils.get_minio_object(TEST_TENANT, "file/wrong_file.json")


@pytest.mark.parametrize(
    "save_object_minio", [({"file_id": 1}, "file_1.json")], indirect=True
)
def test_get_minio_object(monkeypatch, save_object_minio) -> None:
    """Tests that get_minio_object returns correct object with actual size."""
    expected_obj = json.dumps({"file_id": 1})
    monkeypatch.setattr(
        "src.utils.boto3.resource",
        Mock(return_value=save_object_minio),
    )
    data, size = utils.get_minio_object(TEST_TENANT, "file_1.json")
    assert data.read().decode("utf-8") == expected_obj
    assert size == len(expected_obj)
