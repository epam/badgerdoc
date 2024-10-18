from lib.spark_helper.db_service import SparkDBService


def create_db_resources(db_service: SparkDBService, table_name: str) -> None:
    columns = {
        "file_id": "INT",
        "revision_id": "STRING",
        "is_latest": "BOOLEAN",
        "create_date": "TIMESTAMP",
    }
    db_service.create_table_if_not_exists(table_name, columns)


def insert_revision(
    db_service: SparkDBService, table_name: str, file_id: int, revision_id: str
) -> None:
    db_service.insert_table(
        table_name=table_name,
        values=[str(file_id), f'"{revision_id}"', "TRUE", "CURRENT_TIMESTAMP"],
    )
