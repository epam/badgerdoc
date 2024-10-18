# Databricks notebook source
import json

from lib.repository.configs.service import load_config
from lib.repository.ground_truth.stats import StatsCalculator
from lib.spark_helper.ground_truth import GroundTruthFileStorage
from lib.spark_helper.predictions import TemporaryStorage
from lib.spark_helper.storage_service import SparkStorageService

from databricks.sdk.runtime import dbutils

job_ids = json.loads(dbutils.widgets.get("job_ids"))
configs = load_config(project_name=dbutils.widgets.get("project_name"))
storage_service = SparkStorageService(configs)
ground_truth_storage = GroundTruthFileStorage(configs)
temporary_storage = TemporaryStorage(storage_service)

stats = StatsCalculator(temporary_storage, ground_truth_storage)

# COMMAND ----------

stats.avg_summary_by_jobs(job_ids)

# COMMAND ----------

stats.avg_category_by_jobs(job_ids)

# COMMAND ----------

stats.avg_file_by_jobs(job_ids)

# COMMAND ----------

stats.avg_file_and_category_by_jobs(job_ids)
