from typing import Dict, List, Optional, Tuple

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from botocore.response import StreamingBody
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

import src.logger as logger
from src.constants import (
    CONTAINER_NAME,
    DOCKER_REGISTRY_URL,
    DOMAIN_NAME,
    INFERENCE_HOST,
    INFERENCE_PORT,
    MINIO_ACCESS_KEY,
    MINIO_HOST,
    MINIO_PUBLIC_HOST,
    MINIO_SECRET_KEY,
    MODELS_NAMESPACE,
    S3_CREDENTIALS_PROVIDER,
    S3_PREFIX,
)
from src.db import Basement, Model
from src.errors import NoSuchTenant
from src.schemas import DeployedModelPod, MinioHTTPMethod

logger_ = logger.get_logger(__name__)


def convert_bucket_name_if_s3prefix(bucket_name: str) -> str:
    if S3_PREFIX:
        return f"{S3_PREFIX}-{bucket_name}"
    else:
        return bucket_name


def deploy(session: Session, instance: Model) -> None:
    basement_instance = session.query(Basement).get(instance.basement)
    device = "gpu" if basement_instance.gpu_support else "cpu"
    data_path = instance.data_path or {"bucket": "", "file": ""}
    configuration_path = instance.configuration_path or {
        "bucket": "",
        "file": "",
    }
    pod_cpu_limit = basement_instance.limits.get("pod_cpu", "1000m")
    pod_memory_limit = basement_instance.limits.get("pod_memory", "4Gi")
    concurrency_limit = basement_instance.limits.get("concurrency_limit", 1)
    create_ksvc(
        instance.id,
        instance.basement,
        device,
        data_path,
        configuration_path,
        pod_cpu_limit,
        pod_memory_limit,
        concurrency_limit,
    )
    instance.status = "deployed"
    session.commit()


def undeploy(session: Session, instance: Model) -> bool:
    if delete_ksvc(instance.id):
        instance.status = "ready"
        session.commit()
        return True
    return False


def create_ksvc(
    name: str,
    image: str,
    device: str,
    data_path: Dict[str, str],
    config_path: Dict[str, str],
    pod_cpu_limit: str,
    pod_memory_limit: str,
    concurrency_limit: int,
) -> None:
    try:
        config.load_incluster_config()
    except ConfigException:
        config.load_kube_config()
    api = client.CustomObjectsApi()
    if not is_mapping_deployed(name, api):
        create_mapping(name, api)
    my_resource = {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "metadata": {"name": name},
        "spec": {
            "template": {
                "spec": {
                    "containerConcurrency": concurrency_limit,
                    "containers": [
                        {
                            "name": CONTAINER_NAME,
                            "image": f"{DOCKER_REGISTRY_URL}/{image}",
                            "env": [
                                {
                                    "name": "INFERENCE_HOST",
                                    "value": INFERENCE_HOST,
                                },
                                {
                                    "name": "INFERENCE_PORT",
                                    "value": str(INFERENCE_PORT),
                                },
                                {"name": "MINIO_HOST", "value": MINIO_HOST},
                                {
                                    "name": "MINIO_ACCESS_KEY",
                                    "value": MINIO_ACCESS_KEY,
                                },
                                {
                                    "name": "MINIO_SECRET_KEY",
                                    "value": MINIO_SECRET_KEY,
                                },
                                {
                                    "name": "MODEL_NAME",
                                    "value": name,
                                },
                                {"name": "DEVICE", "value": device},
                                {
                                    "name": "DATA_BUCKET",
                                    "value": data_path["bucket"],
                                },
                                {
                                    "name": "DATA_FILE",
                                    "value": data_path["file"],
                                },
                                {
                                    "name": "CONFIG_BUCKET",
                                    "value": config_path["bucket"],
                                },
                                {
                                    "name": "CONFIG_FILE",
                                    "value": config_path["file"],
                                },
                            ],
                            "ports": [
                                {"protocol": "TCP", "containerPort": 8000}
                            ],
                            "resources": {
                                "limits": {
                                    "cpu": pod_cpu_limit,
                                    "memory": pod_memory_limit,
                                },
                            },
                        }
                    ],
                }
            }
        },
    }

    api.create_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace=MODELS_NAMESPACE,
        plural="services",
        body=my_resource,
    )
    return None


def delete_ksvc(name: str) -> bool:
    try:
        config.load_incluster_config()
    except ConfigException:
        config.load_kube_config()
    api = client.CustomObjectsApi()
    try:
        api.delete_namespaced_custom_object(
            "serving.knative.dev", "v1", MODELS_NAMESPACE, "services", name
        )
        if is_mapping_deployed(name, api):
            delete_mapping(name, api)
        return True
    except ApiException:
        return False


def create_mapping(name: str, api: client.CustomObjectsApi) -> None:
    my_resource = {
        "apiVersion": "getambassador.io/v2",
        "kind": "Mapping",
        "metadata": {"name": name, "namespace": MODELS_NAMESPACE},
        "spec": {
            "connect_timeout_ms": 30000,
            "host": f"{name}.{MODELS_NAMESPACE}.{DOMAIN_NAME}",
            "idle_timeout_ms": 50000,
            "prefix": "/",
            "service": name,
            "timeout_ms": 60000,
            "keepalive": {"time": 100, "interval": 10, "probes": 9},
        },
    }

    api.create_namespaced_custom_object(
        group="getambassador.io",
        version="v2",
        namespace=MODELS_NAMESPACE,
        plural="mappings",
        body=my_resource,
    )
    return None


def delete_mapping(name: str, api: client.CustomObjectsApi) -> None:
    api.delete_namespaced_custom_object(
        "getambassador.io", "v2", MODELS_NAMESPACE, "mappings", name
    )
    return None


def is_model_deployed(model_name: str) -> bool:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    api = client.CustomObjectsApi()
    try:
        api.get_namespaced_custom_object(
            group="serving.knative.dev",
            version="v1",
            plural="services",
            namespace=MODELS_NAMESPACE,
            name=model_name,
        )
    except ApiException as api_ex:
        if api_ex.status != 404:
            raise
        return False
    return True


def is_mapping_deployed(model_name: str, api: client.CustomObjectsApi) -> bool:
    try:
        api.get_namespaced_custom_object(
            group="getambassador.io",
            version="v2",
            plural="mappings",
            namespace=MODELS_NAMESPACE,
            name=model_name,
        )
    except ApiException as api_ex:
        if api_ex.status != 404:
            raise
        return False
    return True


def get_pods(model_name: str) -> List[DeployedModelPod]:
    api = client.CoreV1Api()
    pods = []
    all_pods = api.list_namespaced_pod(
        MODELS_NAMESPACE,
        label_selector=f"serving.knative.dev/service={model_name}",
    )
    for pod in all_pods.items:
        if pod.metadata.deletion_timestamp:
            status = "Terminating"
        else:
            status = pod.status.phase
        failures = []
        for container in pod.status.container_statuses:
            if container.name == CONTAINER_NAME:
                try:
                    reason = container.last_state.terminated.reason
                    message = container.last_state.terminated.message
                    failures.append({"reason": reason, "message": message})
                except AttributeError:
                    pass
                try:
                    reason = container.state.waiting.reason
                    message = container.state.waiting.message
                    failures.append({"reason": reason, "message": message})
                except AttributeError:
                    pass
                break
        to_pods = DeployedModelPod(
            name=pod.metadata.name,
            status=status,
            failures=failures,
            start_time=str(pod.status.start_time),
            logs=api.read_namespaced_pod_log(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                container=CONTAINER_NAME,
            ),
        )
        pods.append(to_pods)
    return pods


class NotConfiguredException(Exception):
    pass


def create_boto3_config():
    boto3_config = {}
    if S3_CREDENTIALS_PROVIDER == "minio":
        boto3_config.update(
            {
                "aws_access_key_id": MINIO_ACCESS_KEY,
                "aws_secret_access_key": MINIO_SECRET_KEY,
                "endpoint_url": f"http://{MINIO_HOST}",
            }
        )
    elif S3_CREDENTIALS_PROVIDER == "aws_iam":
        # No additional updates to config needed - boto3 uses env vars
        ...
    else:
        raise NotConfiguredException(
            "s3 connection is not properly configured - "
            "s3_credentials_provider is not set"
        )
    logger_.debug(f"S3_Credentials provider - {S3_CREDENTIALS_PROVIDER}")
    return boto3_config


def get_minio_resource(bucket_name: str) -> boto3.resource:
    """Creates and returns boto3 s3 resource with provided credentials
    to connect minio and validates that Bucket for provided tenant exists.
    If Bucket was not found - raises "NoSuchTenant" exception.
    """
    boto3_config = create_boto3_config()
    s3_resource = boto3.resource(
        "s3", **boto3_config, config=Config(signature_version="s3v4")
    )
    try:
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError as err:
        if "404" in err.args[0]:
            raise NoSuchTenant(f"Bucket {bucket_name} does not exist")
    return s3_resource


def generate_presigned_url(
    http_method: MinioHTTPMethod, bucket_name: str, key: str, expiration: int
) -> Optional[str]:
    """Generates and returns presigned URL for tenant's minio Bucket to make
    actions with Object that has provided "key" in accordance with provided
    http_method. Link is valid for number of "expiration" seconds. In cases
    of boto3 errors returns None.
    """
    minio_client = get_minio_resource(bucket_name).meta.client
    # To make minio accessible via presigned URL from outside the cluster
    # we need to temporary use external host URL for signature generation.
    minio_client.meta._endpoint_url = f"http://{MINIO_PUBLIC_HOST}"
    try:
        presigned_url: str = minio_client.generate_presigned_url(
            http_method,
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expiration,
        )
    except BotoCoreError:
        return None
    minio_client.meta._endpoint_url = f"http://{MINIO_HOST}"
    return presigned_url


def upload_to_object_storage(
    s3_resource: boto3.resource,
    bucket_name: str,
    file: UploadFile,
    file_path: str,
) -> None:
    obj = file.file
    try:
        s3 = s3_resource.Bucket(bucket_name)
        s3.upload_fileobj(Fileobj=obj, Key=file_path)
    except ClientError as err:
        if "404" in err.args[0]:
            raise NoSuchTenant(
                f"Bucket for tenant {bucket_name} does not exist"
            )
        raise


def get_minio_object(bucket: str, key: str) -> Tuple[StreamingBody, int]:
    resource = get_minio_resource(bucket)
    object_data = resource.Object(bucket, key).get()
    return object_data["Body"], object_data["ContentLength"]
