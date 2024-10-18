# Databricks notebook source
import json

import lib.spark_helper.predictions as predictions_helper
from lib.repository.configs.service import load_config
from lib.spark_helper.db_service import SparkDBService
from lib.spark_helper.storage_service import SparkStorageService

from databricks.sdk.runtime import dbutils

configs = load_config(project_name=dbutils.widgets.get("project_name"))
db_service = SparkDBService(configs)
storage_service = SparkStorageService(configs)

permanent_storage = predictions_helper.PermanentStorage(db_service)
temporary_storage = predictions_helper.TemporaryStorage(storage_service)

job_id = json.loads(dbutils.widgets.get("badgerdoc_job_parameters"))["job_id"]
predictions = temporary_storage.load_predictions(job_id=job_id)
permanent_storage.store(predictions)

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from badgerdoc.aiif_develop.predictions order by create_date desc
