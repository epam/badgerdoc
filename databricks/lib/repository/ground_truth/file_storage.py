from json import dumps
from pathlib import Path
from typing import Dict, Union

from lib.spark_helper.storage_service import SparkStorageService


def create_storage_resources(
    storage_service: SparkStorageService, volume_name: str
) -> None:
    storage_service.create_volume_if_not_exists(volume_name)


def write_annotations_to_json(
    storage_service: SparkStorageService,
    annotations: Dict[str, str],
    file_path: Union[Path, str],
) -> None:
    storage_service.write_text(
        data=dumps(annotations, indent=4), file_path=file_path
    )
