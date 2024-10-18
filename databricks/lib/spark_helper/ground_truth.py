import json
from datetime import datetime
from typing import Any, Dict

from lib.spark_helper.db_service import SparkDBService
from lib.spark_helper.storage_service import SparkStorageService


class GroundTruthDBStorage:
    TABLE_NAME = "ground_truth"
    COLUMNS = {
        "file_id": "INT",
        "revision_id": "STRING",
        "is_latest": "BOOLEAN",
        "create_date": "TIMESTAMP",
    }

    def __init__(self, configs: Dict[str, Any]):
        self.db_service = SparkDBService(configs)
        self.create_db_resources()

    def create_db_resources(self) -> None:
        self.db_service.create_table_if_not_exists(
            self.TABLE_NAME, self.COLUMNS
        )

    def set_is_latest_false(self, file_id: int) -> None:
        self.db_service.update_table(
            table_name=self.TABLE_NAME,
            set="is_latest = FALSE",
            filters=f"file_id = {file_id} and is_latest = TRUE",
        )

    def insert_revision(self, file_id: int, revision_id: str) -> None:
        self.db_service.insert_table(
            table_name=self.TABLE_NAME,
            values=[file_id, revision_id, "TRUE", datetime.now()],
        )


class GroundTruthFileStorage:
    VOLUME_NAME = "ground_truth"
    STORAGE_PATH = VOLUME_NAME + "/{file_id}/{revision_id}.json"

    def __init__(self, configs: Dict[str, Any]):
        self.storage_service = SparkStorageService(configs)
        self.create_storage_resources()

    def create_storage_resources(self) -> None:
        self.storage_service.create_volume_if_not_exists(self.VOLUME_NAME)

    def write_annotations_to_json(
        self, file_id: int, revision_id: str, annotations: Dict[str, str]
    ) -> None:

        self.storage_service.write_text(
            data=json.dumps(annotations, indent=4),
            file_path=self.STORAGE_PATH.format(
                file_id=file_id, revision_id=revision_id
            ),
        )

    def read_revision_file(self, file_id: int, revision_id: str) -> Any:

        fpath = self.STORAGE_PATH.format(
            file_id=file_id, revision_id=revision_id
        )

        return json.loads(self.storage_service.read_text(fpath))
