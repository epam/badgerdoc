import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.spark_helper.db_service import SparkDBService
from lib.spark_helper.storage_service import SparkStorageService


@dataclass
class ModelParams:
    run_name: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    temperature: Optional[float] = None
    prompt: Optional[Any] = None
    json_schema: Optional[Any] = None


@dataclass
class Prediction:
    job_id: int
    file_id: int
    ground_truth_revision_id: Optional[str]
    model_params: ModelParams
    prediction_result: Dict[str, Any]
    created_date: datetime


class TemporaryStorage:
    VOLUME_NAME = "predictions"
    STORAGE_PATH = VOLUME_NAME + "/{job_id}/{file_id}.json"

    def __init__(self, storage_service: SparkStorageService) -> None:
        self.storage_service = storage_service
        self.storage_service.create_volume_if_not_exists(self.VOLUME_NAME)

    def store(self, predictions: List[Prediction]) -> None:
        for prediction in predictions:
            prediction_dict = asdict(prediction)
            prediction_dict["created_date"] = (
                prediction.created_date.isoformat()
            )
            self.storage_service.write_text(
                data=json.dumps(prediction_dict, indent=4),
                file_path=Path(
                    self.STORAGE_PATH.format(
                        job_id=prediction.job_id, file_id=prediction.file_id
                    )
                ),
            )

    def load_predictions(self, job_id: int) -> List[Prediction]:

        prediction_file_paths = self.storage_service.list_files(
            Path(f"{self.VOLUME_NAME}/{job_id}")
        )

        predictions = []
        for file_path in prediction_file_paths:
            prediction = json.loads(self.storage_service.read_text(file_path))
            predictions.append(
                Prediction(
                    job_id=prediction["job_id"],
                    file_id=prediction["file_id"],
                    ground_truth_revision_id=prediction[
                        "ground_truth_revision_id"
                    ],
                    model_params=ModelParams(
                        model_name=prediction["model_params"]["model_name"],
                        model_version=prediction["model_params"][
                            "model_version"
                        ],
                        temperature=prediction["model_params"]["temperature"],
                        prompt=prediction["model_params"]["prompt"],
                        json_schema=(
                            json.loads(
                                prediction["model_params"]["json_schema"]
                            )
                            if prediction["model_params"]["json_schema"]
                            else None
                        ),
                    ),
                    prediction_result=prediction["prediction_result"],
                    created_date=datetime.fromisoformat(
                        prediction["created_date"]
                    ),
                )
            )

        return predictions


class PermanentStorage:
    TABLE = "predictions"
    COLUMNS = {
        "job_id": "INT",
        "file_id": "INT",
        "revision_id": "STRING",
        "model_parameters": "STRING",
        "prediction_results": "STRING",
        "create_date": "TIMESTAMP",
    }

    def __init__(self, db_service: SparkDBService):
        self.db_service = db_service
        self.db_service.create_table_if_not_exists(self.TABLE, self.COLUMNS)

    def store(self, predictions: List[Prediction]) -> None:
        for prediction in predictions:
            self.db_service.insert_table(
                self.TABLE,
                [
                    prediction.job_id,
                    prediction.file_id,
                    prediction.ground_truth_revision_id,
                    json.dumps(asdict(prediction.model_params)),
                    json.dumps(prediction.prediction_result),
                    prediction.created_date,
                ],
            )

    def load_by_job_id(
        self,
        job_id: str,
        file_id: Optional[str] = None,
        model_params_run_name: Optional[str] = None,
    ) -> None:
        # return ordered by created_date ascending
        pass
