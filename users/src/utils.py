from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from minio import Minio
from src import config


def extract_idp_data_needed(
    identity_providers_data: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    IDP_aliases = [IDP_data["alias"] for IDP_data in identity_providers_data]
    IDPs_info = []
    for alias in IDP_aliases:
        IDP_info = {
            "Alias": alias,
            "Auth link": f"{config.KEYCLOAK_ENDPOINT}"
            f"/auth/realms/master/protocol/openid-connect/auth?"
            f"client_id=BadgerDoc&response_type=token&"
            f"redirect_uri={config.KEYCLOAK_ENDPOINT}"
            f"/login&kc_idp_hint={alias}",
        }
        IDPs_info.append(IDP_info)

    return IDPs_info


def delete_file_after_7_days(
    client: Minio, days: Optional[int] = 7, prefix: Optional[str] = "coco/"
) -> None:
    """Check files from all buckets with input prefix
    and delete files with old last modified"""
    buckets = client.list_buckets()
    delta = timedelta(days=days)
    today = datetime.now(timezone.utc)
    for bucket in buckets:
        files = client.list_objects(bucket.name, recursive=True, prefix=prefix)
        for file in files:
            if file.last_modified + delta <= today:
                client.remove_object(bucket.name, file.object_name)


def get_bucket_name(tenant: str) -> str:
    return f"{config.S3_PREFIX}-{tenant}" if config.S3_PREFIX else tenant
