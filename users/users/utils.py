from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import users.minio_storage as ms
from users.config import KEYCLOAK_ENDPOINT

minio_client = ms.get_minio_client()


def extract_idp_data_needed(
    identity_providers_data: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    IDP_aliases = [IDP_data["alias"] for IDP_data in identity_providers_data]
    IDPs_info = []
    for alias in IDP_aliases:
        IDP_info = {
            "Alias": alias,
            "Auth link": f"{KEYCLOAK_ENDPOINT}/auth/realms/master/protocol/openid-connect/auth?"
            f"client_id=BadgerDoc&response_type=token&"
            f"redirect_uri={KEYCLOAK_ENDPOINT}/login&kc_idp_hint={alias}",
        }
        IDPs_info.append(IDP_info)

    return IDPs_info


def delete_file_after_7_days(
    days: Optional[int] = 7, prefix: Optional[str] = "coco/"
) -> None:
    """Check files from all buckets with input prefix
    and delete files with old last modified"""
    buckets = minio_client.list_buckets()
    delta = timedelta(days=days)
    today = datetime.now(timezone.utc)
    for bucket in buckets:
        files = minio_client.list_objects(
            bucket.name, recursive=True, prefix=prefix
        )
        for file in files:
            if file.last_modified + delta <= today:
                minio_client.remove_object(bucket.name, file.object_name)
