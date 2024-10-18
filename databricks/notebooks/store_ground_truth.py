# Databricks notebook source
import json

from databricks.sdk.runtime import dbutils

from lib.badgerdoc.service import BadgerDocService
from lib.repository.configs.service import load_config
from lib.repository.ground_truth.helpers import GroundTruthHelper
from lib.repository.ground_truth.revision_factory import RevisionFactory

job_parameters = json.loads(dbutils.widgets.get("badgerdoc_job_parameters"))
tenant = job_parameters["tenant"]
revisions_dict = job_parameters["files_data"]
revisions_dict = [
    revision for revision in revisions_dict if revision.get("revision")
]

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
revisions = RevisionFactory.create_revisions(badgerdoc, tenant, revisions_dict)

# COMMAND ----------

configs = load_config(project_name=dbutils.widgets.get("project_name"))
helper = GroundTruthHelper(configs)

for revision in revisions:
    print(
        f"Inserting file_id: {revision.file_id}, revision_id: {revision.revision_id}"
    )
    helper.insert_latest_revision(revision)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   *
# MAGIC FROM
# MAGIC   badgerdoc.aiif_develop.ground_truth
# MAGIC ORDER BY
# MAGIC   create_date DESC
