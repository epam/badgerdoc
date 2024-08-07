import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import INTEGER, VARCHAR, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from annotation.annotations.main import (
    NotConfiguredException,
    connect_s3,
    convert_bucket_name_if_s3prefix,
    row_to_dict,
)
from annotation.database import Base
from tests.override_app_dependency import TEST_TENANT


class AnnotationRow:
    def __init__(
        self,
        uuid_attr: uuid.UUID,
        datetime_attr: datetime,
        str_attr: str,
        int_attr: int,
    ):
        self.uuid_attr = uuid_attr
        self.datetime_attr = datetime_attr
        self.str_attr = str_attr
        self.int_attr = int_attr


class AnnotationRowTable(Base):
    __tablename__ = "test"

    uuid_attr = Column(UUID(as_uuid=True), primary_key=True)
    datetime_attr = Column(DateTime())
    str_attr = Column(VARCHAR)
    int_attr = Column(INTEGER)


SPECIFIC_DATE_TIME = datetime(2024, 1, 1, 10, 10, 0)

ANNOTATION_ROW = AnnotationRow(
    uuid_attr=uuid.UUID("34c665fd-ddfb-412c-a3f8-3351d87c6030"),
    datetime_attr=SPECIFIC_DATE_TIME,
    str_attr="test string",
    int_attr=1,
)


ANNOTATION_ROW_TABLE = AnnotationRowTable(
    uuid_attr="34c665fd-ddfb-412c-a3f8-3351d87c6030",
    datetime_attr=SPECIFIC_DATE_TIME,
    str_attr="test string",
    int_attr=1,
)


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "row",
        "expected_dictionary",
    ],
    [
        (
            ANNOTATION_ROW_TABLE,
            {
                "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
                "datetime_attr": "2024-01-01T10:10:00",
                "str_attr": "test string",
                "int_attr": 1,
            },
            # row_to_dict won't cast INTEGER to string
        ),
        (
            ANNOTATION_ROW,
            {
                "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
                "datetime_attr": "2024-01-01T10:10:00",
                "str_attr": "test string",
                "int_attr": 1,
            },
            # it return the same as the previous case
        ),
    ],
)
def test_row_to_dict(row, expected_dictionary):
    result = row_to_dict(row)
    print(result)
    assert result == expected_dictionary


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "s3_prefix",
        "bucket_name",
        "expected_string",
    ],
    [
        (
            "S3_test",
            "bucket_test",
            "S3_test-bucket_test",
        ),
        (
            None,
            "bucket_test",
            "bucket_test",
        ),
    ],
)
def test_convert_bucket_name_if_s3prefix(
    monkeypatch,
    s3_prefix,
    bucket_name,
    expected_string,
):
    monkeypatch.setattr("annotation.annotations.main.S3_PREFIX", s3_prefix)
    result = convert_bucket_name_if_s3prefix(bucket_name=bucket_name)
    assert result == expected_string


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "s3_provider",
        "bucket_name",
    ],
    [
        (
            "minio",
            TEST_TENANT,
        ),  # successful connection
        (
            "aws_iam",
            TEST_TENANT,
        ),  # successful connection
        (
            "no_provider",
            TEST_TENANT,
        ),  # NotConfiguredException
        (
            "aws_iam",
            "no_bucket",
        ),  # NoSuchBucket
    ],
)
def test_connect_s3(moto_s3, monkeypatch, s3_provider, bucket_name):
    mock_resource = MagicMock(return_value=moto_s3)
    monkeypatch.setattr("boto3.resource", mock_resource)

    monkeypatch.setattr("annotation.annotations.main.S3_PROVIDER", s3_provider)

    if s3_provider == "no_provider":
        with pytest.raises(NotConfiguredException):
            connect_s3(bucket_name)
    elif bucket_name == "no_bucket":
        with pytest.raises(moto_s3.meta.client.exceptions.NoSuchBucket):
            connect_s3(bucket_name)
    else:
        result_s3 = connect_s3(bucket_name)
        assert moto_s3 == result_s3
