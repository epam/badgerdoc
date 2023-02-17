import pytest
from pydantic import ValidationError

from models import schemas
from tests.test_utils import TEST_LIMITS


def test_empty_id_in_modelbase_raises_error():
    minio_path = {"file": "file", "bucket": "bucket"}
    with pytest.raises(ValidationError, match="this value has at least 1 characters"):
        schemas.ModelWithId(
            id="",
            name="name",
            basement="base",
            data_path=minio_path,
            configuration_path=minio_path,
            categories=["any"],
        )


def test_validation_of_model_id():
    minio_path = {"file": "file", "bucket": "bucket"}
    long_id = 16 * "a"
    with pytest.raises(
        ValidationError,
        match="Incorrect resource name."
        " Use at most 15 ascii lowercase letters,"
        " - and numbers, start it with letter or number.",
    ):
        schemas.ModelWithId(
            id=long_id,
            name="n",
            basement="base",
            data_path=minio_path,
            configuration_path=minio_path,
            categories=["any"],
        )
    capslock_id = "Name"
    with pytest.raises(
        ValidationError,
        match="Incorrect resource name."
        " Use at most 15 ascii lowercase letters,"
        " - and numbers, start it with letter or number.",
    ):
        schemas.ModelWithId(
            id=capslock_id,
            name="n",
            basement="base",
            data_path=minio_path,
            configuration_path=minio_path,
            categories=["any"],
        )
    underscore_id = "a_"
    with pytest.raises(
        ValidationError,
        match="Incorrect resource name."
        " Use at most 15 ascii lowercase letters,"
        " - and numbers, start it with letter or number.",
    ):
        schemas.ModelWithId(
            id=underscore_id,
            name="n",
            basement="base",
            data_path=minio_path,
            configuration_path=minio_path,
            categories=["any"],
        )
    space_id = "a "
    with pytest.raises(
        ValidationError,
        match="Incorrect resource name. "
        "Use at most 15 ascii lowercase letters,"
        " - and numbers, start it with letter or number",
    ):
        schemas.ModelWithId(
            id=space_id,
            name="n",
            basement="base",
            data_path=minio_path,
            configuration_path=minio_path,
            categories=["any"],
        )
    wrong_start_id = "-name"
    with pytest.raises(
        ValidationError,
        match="Incorrect resource name. "
        "Use at most 15 ascii lowercase letters,"
        " - and numbers, start it with letter or number",
    ):
        schemas.ModelWithId(
            id=wrong_start_id,
            name="n",
            basement="base",
            data_path=minio_path,
            configuration_path=minio_path,
            categories=["any"],
        )
    correct_id = "a-6"
    schemas.ModelWithId(
        id=correct_id,
        name="n",
        basement="base",
        data_path=minio_path,
        configuration_path=minio_path,
        categories=["any"],
    )


def test_empty_id_in_basementbase_raises_error():
    with pytest.raises(ValidationError, match="this value has at least 1 characters"):
        schemas.BasementBase(id="", name="base", gpu_support=True)


def test_not_empty_id_in_basementbase_does_not_raise_error():
    schemas.BasementBase(id="1", name="base", gpu_support=True, limits=TEST_LIMITS)


def test_validation_of_bucket_in_minio_path():
    underscore_bucket = "bucket_"
    with pytest.raises(ValidationError, match="Bucket cannot contain underscores"):
        schemas.MinioPath(bucket=underscore_bucket, file="file")
    correct_bucket = "bucket"
    schemas.MinioPath(bucket=correct_bucket, file="file")
