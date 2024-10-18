from typing import Any, Dict, List

from databricks.sdk.runtime import spark


class SparkDBService:
    def __init__(self, configs: Dict[str, Any]):
        self._configs = configs
        self._catalog = self._configs["databricks"]["catalog"]
        self._schema = self._configs["databricks"]["schema"]

    def create_table_if_not_exists(
        self, table_name: str, columns: Dict[str, str]
    ) -> None:
        columns_str = ", ".join(
            [f"{col} {col_type}" for col, col_type in columns.items()]
        )
        create_table = (
            f"CREATE TABLE IF NOT EXISTS {self._catalog}.{self._schema}.{table_name} "
            f"({columns_str})"
        )
        spark.sql(create_table)

    def update_table(self, table_name: str, set: str, filters: str) -> None:

        query = f"""
            UPDATE {self._catalog}.{self._schema}.{table_name}
            SET {set}
            WHERE {filters}
        """
        spark.sql(query)

    def insert_table(self, table_name: str, values: List[Any]) -> None:

        placeholders = ", ".join(["?"] * len(values))
        query = f"""
            INSERT INTO {self._catalog}.{self._schema}.{table_name}
            VALUES ({placeholders})
        """
        spark.sql(query, values)
