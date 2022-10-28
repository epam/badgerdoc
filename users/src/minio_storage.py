from typing import Optional

import src.config as config
from minio import Minio


def get_minio_client() -> Optional[Minio]:
    """Return Minio client if URI is provided via config.py."""
    if not config.MINIO_URI:
        return None
    return Minio(
        endpoint=config.MINIO_URI,
        access_key=config.MINIO_ACCESS_KEY,
        secret_key=config.MINIO_SECRET_KEY,
        secure=False,
    )


def create_bucket(
    client: Minio,
    bucket_name: str,
    location: str = "us-east-1",
    object_lock: bool = False,
) -> None:
    """Create minio bucket."""
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name, location, object_lock)
