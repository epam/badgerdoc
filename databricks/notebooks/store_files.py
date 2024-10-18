# Databricks notebook source
import json

import requests
from lib.repository.configs.service import load_config
from lib.spark_helper.files import FilesStorage

from databricks.sdk.runtime import dbutils

configs = load_config(project_name=dbutils.widgets.get("project_name"))
files_storage = FilesStorage(configs)

job_parameters = json.loads(dbutils.widgets.get("badgerdoc_job_parameters"))
for file in job_parameters["files_data"]:
    file_id = int(file["file_id"])
    print(f"Saving file_id: {file_id}")

    response = requests.get(
        file["signed_url"] if "signed_url" in file else file["s3_signed_url"]
    )

    files_storage.store_pdf(response.content, file_id)
    files_storage.store_text(response.content, file_id)
