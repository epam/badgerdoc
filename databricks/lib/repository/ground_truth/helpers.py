from typing import Any, Dict, Optional

from lib.repository.ground_truth.models import Revision
from lib.spark_helper.ground_truth import (
    GroundTruthDBStorage,
    GroundTruthFileStorage,
)
from pyspark.sql import functions as F

from databricks.sdk.runtime import spark


class GroundTruthHelper:
    def __init__(self, configs: Dict[str, Any]) -> None:
        self._configs = configs
        self.db_storage = GroundTruthDBStorage(configs)
        self.file_storage = GroundTruthFileStorage(configs)

    def insert_latest_revision(self, revision: Revision) -> None:

        self.db_storage.set_is_latest_false(revision.file_id)
        self.db_storage.insert_revision(revision.file_id, revision.revision_id)
        self.file_storage.write_annotations_to_json(
            file_id=revision.file_id,
            revision_id=revision.revision_id,
            annotations=revision.annotations,
        )

    def get_latest_revision_id(self, file_id: int) -> Optional[str]:

        catalog = self._configs["databricks"]["catalog"]
        schema = self._configs["databricks"]["schema"]

        table = f"{catalog}.{schema}.{GroundTruthDBStorage.TABLE_NAME}"
        spdf_annotations = spark.table(table)
        latest_revision_id = spdf_annotations.filter(
            (F.col("file_id") == file_id) & (F.col("is_latest") == True)
        ).first()

        if not latest_revision_id:
            print(f"Warning: No latest revision found for file_id: {file_id}")
            return None

        return str(latest_revision_id["revision_id"])
