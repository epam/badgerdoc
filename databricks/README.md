# Badgerdoc Databricks 
Badgerdoc Databricks is designed to streamline the development of machine learning pipelines on the Databricks platform. It includes a collection of built-in notebooks that accelerate the process, enabling you to manage tasks such as annotation storage, predictions, model performance evaluation, and model comparison. This module allows you to focus on the critical elements of machine learning, like the prediction notebook, while leveraging pre-existing notebooks for the rest of the pipeline.

## How to use
Below is a step-by-step guide to setting up a basic Databricks pipeline to store Badgerdoc annotations in Unity Catalog.

### 1. Add project configs
Add your project-specific configurations in `/databricks/config.yaml`. This file allows you to define multiple environments, such as development and production. The project name from this file will be referenced in the job parameters to apply the relevant configurations in your notebooks. Here's an example configuration file for both development and production environments with the minimum required settings:

```yaml
# config.yaml
sample_project_dev: # this is project_name in job parameters
  databricks:
    catalog: unity_catalog_name_dev
    schema: unity_catalog_schema_dev

sample_project_prod:
  databricks:
    catalog: unity_catalog_name_prod
    schema: unity_catalog_schema_prod
```

### 2. Set Up Secrets
First [create a secret scope](https://docs.databricks.com/en/security/secrets/secret-scopes.html) and then [add the required credentials](https://docs.databricks.com/en/security/secrets/secrets.html) to this secret scope. In this example, we set the secret scope name to match the project name, `sample_project_dev`. You may create separate scopes for development and production environments. The secret scope name will be specified in the job parameters, allowing your notebooks to access the correct credentials. The following secret keys are required for Badgerdoc communication:

* `badgerdoc_host`
* `badgerdoc_username`
* `badgerdoc_password`

Additional secrets can be added as needed based on your project requirements.

### 3. Create a Databricks Workflow
Within Databricks:
1. Navigate **Workflows** and then click **Create Job**. 
2. Select `/databricks/notebooks/store_ground_truth` notebook as *Path
3. Set Job Parameters
   * `project_name`: `sample_project_dev`
   * `secrets_scope`: `sample_project_dev`

### 4. Trigger workflow from Badgerdoc
Within Badgerdoc:
1. Navigate **Jobs** and then click **New Job**.
2. Select the documents you want to store the ground truths the click **Next**
3. Choose **Databricks** as the Pipeline Manager.
4. Select the pipeline you created in Step 3 and create the job by clicking **New Job**.

Once the Badgerdoc job is created, your Databricks pipeline will be triggered. The `store_ground_truth` notebook will set up all the necessary resources within Unity Catalog. You can create a new folder under `/databricks/notebooks` for any project-specific implementations. You can efficiently construct pipelines by combining your project-specific notebooks with the built-in generic ones.


