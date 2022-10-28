# Job Manager

Creates Extraction Job or Annotation Job and triggers its execution in the Inference Pipeline Manager
or Annotation microservice respectively.
Please also change POSTGRESQL_JOBMANAGER_DATABASE_URI env in Dockerfile.

## Setup
`docker build -t job_manager .`

`docker run -p 8123:8123 job_manager`

## Config
.env file for settings.
Change all variables in accordance to your setup
### App settings
| Variable | Description |
|---|---------------|
|`str` <br/> PIPELINE_MANAGER_URI | URI of the Inference Pipeline Manager microservice |
|`str` <br/> DATASET_MANAGER_URI | URI of the Dataset Manager microservice |
|`str` <br/> ANNOTATION_MICROSERVICE_URI | URI of the Annotation microservice |
|`str` <br/> POSTGRESQL_JOBMANAGER_DATABASE_URI | URI of database to work with. Should have format postgresql+psycopg2://user:password@host:port/db_name |
|`int` <br/> PAGINATION_THRESHOLD| Maximum number of pages in one batch of files data to pass it into Inference Pipeline Manager or Annotation microservice |
