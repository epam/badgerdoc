# Databricks notebook source
import json
import random
from typing import Any, Dict, Generator, List, Tuple

from databricks.sdk.runtime import dbutils

import lib.spark_helper.predictions as predictions_helper
from lib.badgerdoc.service import BadgerDocService
from lib.repository.configs.service import load_config
from lib.spark_helper.storage_service import SparkStorageService

configs = load_config(project_name=dbutils.widgets.get("project_name"))

storage_service = SparkStorageService(configs)
temporary_storage = predictions_helper.TemporaryStorage(storage_service)

job_parameters = json.loads(dbutils.widgets.get("badgerdoc_job_parameters"))


# COMMAND ----------
def gpt_to_badgerdoc_annotation(
    gpt_key: str, gpt_value: Any
) -> Generator[Tuple[str, str], None, None]:
    default_str = "unknown"
    if gpt_key == "patient_information":
        age = gpt_value.get("age", default_str)
        age_unit = gpt_value.get("age_unit", "age_unit")
        gender = gpt_value.get("gender", default_str)
        ethnic_group = gpt_value.get("ethnic_group", default_str)
        autopsy_done = gpt_value.get("autopsy_done", default_str)
        pregnant = gpt_value.get("pregnant", default_str)
        yield (
            gpt_key,
            f"Age: {age} {age_unit}\nGender: {gender}\nEthnic group: {ethnic_group}",
        )
        yield ("age", age)
        yield ("gender", gender)
        yield ("autopsy_done", autopsy_done)
        yield ("pregnant", pregnant)
        yield ("ethnic_group", ethnic_group)
    elif gpt_key == "patient_examination":
        for examination in gpt_value:
            yield (gpt_key, f"{examination}")
    elif gpt_key == "patient_lab_tests":
        for lab_test in gpt_value:
            assessment = lab_test.get("assessment", default_str)
            result = lab_test.get("result", default_str)
            result_unit = lab_test.get("result_unit", default_str)
            yield ("assessment", assessment)
            yield ("assessment_result", f"{result} {result_unit}")

    elif gpt_key == "initial_conidition":
        for condition in gpt_value:
            yield ("reported_term_local", condition.get("reported_term_local"))


def extract_objs(gpt: List[Dict[str, Any]]) -> List[dict[str, Any]]:
    bd_objs = []
    for needle in gpt:
        for gpt_key, gpt_value in needle.items():
            for category, bd_value in gpt_to_badgerdoc_annotation(
                gpt_key, gpt_value
            ):
                if category:
                    bd_objs.append(
                        {
                            "id": random.choice(range(0, 0xFFFFFF)),
                            "category": category,
                            "type": "document",
                            "text": bd_value,
                        }
                    )

    return bd_objs


def list_conv(obj: Any) -> Any:
    return obj if obj.__class__ == list else [obj]


def create_annotation_body(gpt_output: Any) -> Dict[str, Any]:
    return {
        "base_revision": None,
        "user": None,
        "pipeline": 0,
        "pages": [
            {
                "page_num": 1,
                "size": {
                    "width": 0,
                    "height": 0,
                },
                "objs": extract_objs(list_conv(gpt_output)),
            }
        ],
    }


# COMMAND ----------
secrets_scope = dbutils.widgets.get("secrets_scope")

badgerdoc = BadgerDocService(
    host=dbutils.secrets.get(scope=secrets_scope, key="badgerdoc_host"),
    username=dbutils.secrets.get(
        scope=secrets_scope, key="badgerdoc_username"
    ),
    password=dbutils.secrets.get(
        scope=secrets_scope, key="badgerdoc_password"
    ),
)

# COMMAND ----------

tenant = job_parameters["tenant"]
job_id = job_parameters["job_id"]

predictions = temporary_storage.load_predictions(job_id=job_id)

for prediction in predictions:
    badgerdoc_commit_body = create_annotation_body(
        prediction.prediction_result
    )
    badgerdoc.commit_annotation(
        tenant, job_id, prediction.file_id, badgerdoc_commit_body
    )
