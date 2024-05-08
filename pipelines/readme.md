# PipelineExecutor

Executor for pipelines.

## Setup
`docker build -t pipelines .`

`docker run -p 8080:8080 --name <name> pipelines`

## Config
.env file is responsible for the app settings.
### App settings
| Variable | Description |
|---|---------------|
|`int` <br/> `default: 15` <br/> HEARTBEAT_TIMEOUT | How often heartbeat checker goes to the db, seconds. |
|`int` <br/> `default: 10` <br/> HEARTBEAT_THRESHOLD_MUL| Set maximum timedelta of last heartbeat. More than HEARTBEAT_TIMEOUT * HEARTBEAT_THRESHOLD_MUL = heartbeat is dead. |
|`int` <br/> `default: 5` <br/> RUNNER_TIMEOUT | How often pipeline runner check pending tasks in the db, seconds. |
|`int` <br/> `default: 15` <br/> MAX_WORKERS| Maximum concurrent pipeline executions. |
|`str` <br/> `default: ""` <br/> ANNOTATION_URI| Annotation Manager annotation endpoint. |
|`str` <br/> `default: ""` <br/> PROCESSING_URI| Postprocessor postprocessing endpoint. |
|`bool` <br/> `default: False` <br/> DEBUG_MERGE| Models inference data deletion in Minio after pipeline execution. Don't delete if True. |

### SQLAlchemy settings
| Variable | Description |
|---|---------------|
|`int` <br/> `default: 0` <br/> SA_POOL_SIZE | Limit of the open connections. If 0, no limit. |

### PostgreSQL settings
| Variable | Description |
|---|---------------|
|`str` <br/> `default: postgres` <br/> POSTGRES_USER| Server username. |
|`str` <br/> `default: admin` <br/> POSTGRES_PASSWORD| Server password. |
|`str` <br/> `default: localhost` <br/> POSTGRES_HOST| Server host. |
|`int` <br/> `default: 5432` <br/> POSTGRES_PORT| Server port. |
|`int` <br/> `default: pipelines` <br/> POSTGRES_DB| Database name. |

### S3 settings
File storage for result processing.

| Variable | Description |
|---|---------------|
|`str` <br/> `default: None` <br/> S3_PROVIDER| Credentials provider. Support `minio`, `aws_iam`, `aws_env`, `aws_config` |
|`str` <br/> `default: ""` <br/> S3_PREFIX| Bucket name prefix. `<S3_PREFIX>[-]bucket_name` |
|`str` <br/> `default: None` <br/> S3_ENDPOINT| S3 storage URI |
|`str` <br/> `default: None` <br/> S3_ACCESS_KEY| S3 storage access key |
|`str` <br/> `default: None` <br/> S3_SECRET_KEY| S3 storage secret key |
|`str` <br/> `default: None` <br/> AWS_PROFILE| AWS_PROFILE if `aws_config` provider selected |
