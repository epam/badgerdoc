import os
from pathlib import Path
from typing import Any, Dict, List

from databricks.sdk.runtime import spark


class SparkStorageService:
    def __init__(self, configs: Dict[str, Any]):
        self._configs = configs
        self._catalog = self._configs["databricks"]["catalog"]
        self._schema = self._configs["databricks"]["schema"]

    def create_volume_if_not_exists(self, volume_name: str) -> None:

        create_volume = f"CREATE VOLUME IF NOT EXISTS {self._catalog}.{self._schema}.{volume_name}"

        spark.sql(create_volume)

    def list_files(self, file_path: Path | str) -> List[Path]:

        file_path = (
            Path(f"/Volumes/{self._catalog}/{self._schema}") / file_path
        )

        return list(file_path.iterdir())

    def read_text(self, file_path: Path | str) -> str:

        file_path = (
            Path(f"/Volumes/{self._catalog}/{self._schema}") / file_path
        )

        with open(file_path, "r") as file:
            return file.read()

    def write_text(self, data: str, file_path: Path | str) -> None:

        file_path = (
            Path(f"/Volumes/{self._catalog}/{self._schema}") / file_path
        )

        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "w") as file:
            file.write(data)

    def write_binary(self, data: bytes, file_path: Path | str) -> None:

        file_path = (
            Path(f"/Volumes/{self._catalog}/{self._schema}") / file_path
        )

        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "wb") as file:
            file.write(data)
