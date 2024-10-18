# Databricks notebook source
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import lib.spark_helper.predictions as predictions_helper
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import SecretStr
from langchain_openai import AzureChatOpenAI
from lib.repository.configs.service import load_config
from lib.repository.ground_truth.helpers import GroundTruthHelper
from lib.spark_helper.files import FilesStorage
from lib.spark_helper.storage_service import SparkStorageService

from databricks.sdk.runtime import dbutils

# COMMAND ----------

system_prompt = [
    (
        "system",
        "You are an assistant that extracts product information",
    ),
    ("human", "{text}"),
]


json_schema = {
    "title": "ProductInfo",
    "description": "Information about a product",
    "type": "object",
    "properties": {
        "price": {
            "type": "string",
            "description": "Price of a product in USD",
        },
    },
}


# COMMAND ----------


def get_model(
    credentials: Dict[str, str], parameters: predictions_helper.ModelParams
) -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=credentials["azure_endpoint"],
        api_key=SecretStr(credentials["api_key"]),
        azure_deployment=parameters.model_name,
        api_version=parameters.model_version,
        temperature=parameters.temperature if parameters.temperature else 1.0,
    )


def predict(
    model: AzureChatOpenAI, text: str, output_schema: Dict[Any, Any]
) -> Any:
    prompt = ChatPromptTemplate.from_messages(system_prompt)

    runnable = prompt | model.with_structured_output(schema=output_schema)
    predictions = runnable.invoke({"text": text})

    return predictions


# COMMAND ----------

configs = load_config(project_name=dbutils.widgets.get("project_name"))
storage_service = SparkStorageService(configs)


def predict_file(
    model: AzureChatOpenAI, file: Dict[Any, Any], output_schema: Dict[Any, Any]
) -> Any:
    file_id = file["file_id"]
    print(f"Predicting file: {file_id}")

    text = storage_service.read_text(
        Path(FilesStorage.TXT_STORAGE_PATH.format(file_id=file_id))
    )
    prediction = predict(model, text, output_schema)

    return prediction


def predict_files_parallel(
    model: AzureChatOpenAI,
    files: List[Dict[Any, Any]],
    output_schema: Dict[Any, Any],
) -> List[Dict[Any, Any]]:

    predictions = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_file = {
            executor.submit(predict_file, model, file, output_schema): file
            for file in files
        }
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            prediction = future.result()
            predictions.append(
                {
                    "file_id": int(file["file_id"]),
                    "prediction": prediction,
                }
            )

    return predictions


# COMMAND ----------

secrets_scope = dbutils.widgets.get("secrets_scope")
model_credentials = {
    "azure_endpoint": dbutils.secrets.get(
        scope=secrets_scope, key="gpt_endpoint"
    ),
    "api_key": dbutils.secrets.get(
        scope=secrets_scope, key="azure_openai_api_key"
    ),
}
model_parameters = predictions_helper.ModelParams(
    model_name="gpt-4",
    model_version="2023-12-01-preview",
    temperature=0,
    prompt=system_prompt,
    json_schema=json.dumps(json_schema),
)

# COMMAND ----------

helper = GroundTruthHelper(configs)
job_parameters = json.loads(dbutils.widgets.get("badgerdoc_job_parameters"))
files = job_parameters["files_data"]

model = get_model(model_credentials, model_parameters)
predicted_values = predict_files_parallel(model, files, json_schema)

predictions: list[predictions_helper.Prediction] = []
for predicted_value in predicted_values:
    file_id = predicted_value["file_id"]
    predictions.append(
        predictions_helper.Prediction(
            job_id=int(job_parameters["job_id"]),
            file_id=file_id,
            ground_truth_revision_id=helper.get_latest_revision_id(file_id),
            model_params=model_parameters,
            prediction_result=predicted_value["prediction"],
            created_date=datetime.now(),
        )
    )

temporary_storage = predictions_helper.TemporaryStorage(storage_service)
temporary_storage.store(predictions)
