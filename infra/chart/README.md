# How to install minimal badgedoc app

## Prerequisites

1. PostgreSQL database host, port, credentials per service
2. Access to S3

## How to install

set values in values.yaml

run in shell
```shell
helm install --debug --dry-run badgerdoc .
```

### Configuration of values

| Parameter                          | Description        | Default                                          |
|------------------------------------|--------------------|--------------------------------------------------|
| affinity | | null
| labels | | null
| nodeSelector | | null
| tolerations | | null
| podAnnotations | | sidecar.istio.io/inject | | "false"
| dbHost | | postgres-postgresql
| dbPort | | 5432
| s3CredentialsProvider | | "aws_iam"
| s3Endpoint | | "minio"
| host | | yourexample.com
| imagePullPolicy | | Always
| serviceAccountName | | null
| automountToken | | false
| replicaCount | | 1
| resources | | {}
| schedulerName | | default-scheduler
| servicePort | | 80
| serviceType | | ClusterIP
| updateStrategy | | {}

Global parameter works only if the local chart parameter is null.

### Values per service

| Parameter                          | Description        | Default                                          |
|------------------------------------|--------------------|--------------------------------------------------|
imageName | | ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/badgerdoc
imageTag | | latest
dbName | | ${DATABASENAME}
keycloak.externalUrl | | "http://example.com"
keycloak.internalUrl | | "http://bagerdoc-keycloak"
secret.enabled | | true
secret.dbuser | | "postgres"
secret.dbpassword | | "postgres"
secret.s3user | | "serviceuser"
secret.s3password | | "12345678"

See [values.yaml](values.yaml)