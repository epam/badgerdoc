from unittest.mock import patch

import minio
import pytest

from src import s3


def test_get_minio_client():
    """Testing get_minio_client."""
    assert isinstance(s3.get_minio_client(), minio.Minio)


@pytest.mark.parametrize(
    ("prefix", "bucket", "expected"),
    (
        ("", "tenant", "tenant"),
        ("", "some-tenant", "some-tenant"),
        ("prefix", "prefix-tenant", "tenant"),
        ("prefix", "prefix-prefix-tenant", "prefix-tenant"),
    ),
)
def test_tenant_from_bucket(prefix: str, bucket: str, expected: str) -> None:
    with patch("src.config.S3_PREFIX", prefix):
        assert s3.tenant_from_bucket(bucket) == expected
