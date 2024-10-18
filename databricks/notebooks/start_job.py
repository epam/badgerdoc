# Databricks notebook source
import json

from lib.badgerdoc.service import BadgerDocService

from databricks.sdk.runtime import dbutils

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

job_parameters = json.loads(dbutils.widgets.get("badgerdoc_job_parameters"))
tenant = job_parameters["tenant"]
job_id = job_parameters["job_id"]

badgerdoc.start_job(tenant, job_id)
