## Prerequisites:

* k8s
* kubectl
* helm
* elasticsearch
* postresql
* keycloak backup db restored (this file can be retrieved from devops team)

###### Create DBs in your postregsql

```roomsql
create database annotation;
create database job_manager;
create database file_management;
create database models;
create database pipelines;
create database processing;
create database users;
create database scheduler;
create database keycloak;
```

###### Restore the db (will be fixed soon)
```shell
cat keycloak.sql | psql -U postgres keycloak
```

```
As for now it would be better to use only one user/password for all databases.
Keycloak config from scratch will be provided soon.
```

## Installation:

```shell
helm repo add datawire https://www.getambassador.io
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

##### Ambassador
```shell
kubectl apply -f infra/k8s/helm/ambassador/aes-crds.yaml
kubectl create namespace ambassador
helm install ambassador --namespace ambassador datawire/ambassador --version "6.9.3" -f infra/k8s/helm/ambassador/ambassador.values.yaml
kubectl patch deployment ambassador -n ambassador --patch "$(cat infra/k8s/helm/ambassador/ambassador.patch.yaml)"
kubectl apply -f infra/k8s/helm/ambassador/ambassador.host.yaml
kubectl apply -f infra/k8s/helm/ambassador/ambassador.module.yaml
```

##### Istio

```shell
export ISTIO_VERSION=1.11.4
curl -sL https://istio.io/downloadIstioctl | sh -
$HOME/.istioctl/bin/istioctl manifest install -y -f - <<EOF
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    extensionProviders:
    - name: oauth2-proxy
      envoyExtAuthzHttp:
        service: oauth2-proxy.oauth2-proxy.svc.cluster.local
        port: 4180
        includeRequestHeadersInCheck:
        - cookie
        headersToUpstreamOnAllow:
        - authorization
        headersToDownstreamOnDeny:
        - set-cookie
EOF
 Replace istio-ingressgateway with NodePort:
kubectl delete svc istio-ingressgateway -n istio-system
sleep 1
kubectl apply -f infra/k8s/helm/istio/patched_istio_svc.yaml
```

##### Knative

```shell
kubectl create ns knative-serving
kubectl apply -f badgerdoc_infra_k8s/knative/operator.yaml
sleep 10
kubectl apply -f infra/k8s/knative/knative_serving.yaml
kubectl apply -f infra/k8s/knative/domain.configuration.yaml
kubectl label namespace knative-serving istio-injection=enabled
kubectl label namespace default istio-injection=enabled
```

##### Create Namespace for Application

```shell
kubectl create ns app
kubectl label namespace app istio-injection=enabled
```

##### Deploy Keycloak

Please, set up DB host, user, password
```shell
helm install bagerdoc-keycloack -n app -f values.yaml --version 6.0.1 --set  externalDatabase.password=postgres --set externalDatabase.user=postgres  --set externalDatabase.host=postgres-postgresql bitnami/keycloak

#replace the host name in mapping first
kubectl apply -f infra/helm/keycloack/mapping.yaml
```

Keycloak must have the same host name  outside and inside k8s cluster

```shell
kubectl -n kube-system edit configmap coredns 
```
Please add  rewrite rule to coredns config
```
rewrite name app.badgerdoc.com ambassador.ambassador.svc.cluster.local
```
Related issue: https://github.com/coredns/coredns/issues/3298#issuecomment-534472063

##### apache kafka

```shell
cd infra/helm/apache-kafka
helm install kafka -n app -f values.yaml --version 15.0.1  bitnami/kafka
```

##### gotenberg

```shell
cd infra/helm/gotenberg
helm install gotenberg .  --namespace app
```

##### Create secrets

Please set all variables first. Some of the secrets were taken from keycloak.

MINIO secrets can be repalced with S3 endpoint and AWS credentials.

${DEPLOY_ENV} is the namespace, for example 'app'

```shell
kubectl delete secret -n ${DEPLOY_ENV} annotation --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic annotation --from-literal=POSTGRES_USER=${ANNOTATION_POSTGRES_USER} --from-literal=POSTGRES_PASSWORD=${ANNOTATION_POSTGRES_PASSWORD} --from-literal=S3_LOGIN=${ANNOTATION_S3_LOGIN} --from-literal=S3_PASS=${ANNOTATION_S3_PASS}

kubectl delete secret -n ${DEPLOY_ENV} assets --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic assets --from-literal=POSTGRES_USER=${DATASET_POSTGRES_USER} --from-literal=POSTGRES_PASSWORD=${DATASET_POSTGRES_PASSWORD} --from-literal=MINIO_ACCESS_KEY=${DATASET_MINIO_ACCESS_KEY} --from-literal=MINIO_SECRET_KEY=${DATASET_MINIO_SECRET_KEY} --from-literal=DATABASE_URL=${DATASET_DATABASE_URL} --from-literal=JWT_SECRET=${ASSETS_JWT_SECRET}

kubectl delete secret -n ${DEPLOY_ENV} jobs --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic jobs --from-literal=POSTGRESQL_JOBMANAGER_DATABASE_URI=${JOBMANAGER_POSTGRESQL_DATABASE_URI}

kubectl delete secret -n ${DEPLOY_ENV} pipelines --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic pipelines --from-literal=DB_USERNAME=${INFERENCE_MANAGER_DB_USERNAME} \
--from-literal=DB_PASSWORD=${INFERENCE_MANAGER_DB_PASSWORD} --from-literal=DB_URL=${INFERENCE_MANAGER_DB_URL} \
--from-literal=MINIO_ACCESS_KEY=${PIPELINES_MINIO_ACCESS_KEY} --from-literal=MINIO_SECRET_KEY=${PIPELINES_MINIO_SECRET_KEY} \
--from-literal=PIPELINES_CLIENT_SECRET_KEY_DEV1=${PIPELINES_CLIENT_SECRET_KEY_DEV1} \

kubectl delete secret -n ${DEPLOY_ENV} search --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic search --from-literal=S3_LOGIN=${SEARCH_S3_LOGIN} --from-literal=S3_PASS=${SEARCH_S3_PASS}

kubectl delete secret -n ${DEPLOY_ENV} preprocessing --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic preprocessing --from-literal=MINIO_ROOT_USER=${PREPROCESSING_MINIO_ROOT_USER} --from-literal=MINIO_ROOT_PASSWORD=${PREPROCESSING_MINIO_ROOT_PASSWORD}

kubectl delete secret -n ${DEPLOY_ENV} models --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic models --from-literal=POSTGRES_USER=${MODELS_POSTGRES_USER} --from-literal=POSTGRES_PASSWORD=${MODELS_POSTGRES_PASSWORD} --from-literal=MINIO_ACCESS_KEY=${MODELS_MINIO_ACCESS_KEY} --from-literal=MINIO_SECRET_KEY=${MODELS_MINIO_SECRET_KEY} --from-literal=DATABASE_URL=${MODELS_DATABASE_URL}

kubectl delete secret -n ${DEPLOY_ENV} users --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic users --from-literal=POSTGRES_USER=${USERS_POSTGRES_USER} \
--from-literal=POSTGRES_PASSWORD=${USERS_POSTGRES_PASSWORD} \
--from-literal=MINIO_ACCESS_KEY=${USERS_MINIO_ACCESS_KEY} \
--from-literal=MINIO_SECRET_KEY=${USERS_MINIO_SECRET_KEY} \
--from-literal=DATABASE_URL=${USERS_DATABASE_URL} \
--from-literal=KEYCLOAK_DIRECT_ENDPOINT_DEV1=${KEYCLOAK_DIRECT_ENDPOINT_DEV1} \
--from-literal=BADGERDOC_CLIENT_SECRET_DEV1=${BADGERDOC_CLIENT_SECRET_DEV1} \
--from-literal=ADMIN_CLIENT_SECRET_DEV1=${ADMIN_CLIENT_SECRET_DEV1} \
kubectl delete secret -n ${DEPLOY_ENV} processing --ignore-not-found
kubectl create secret -n ${DEPLOY_ENV} generic processing --from-literal=MINIO_ROOT_USER=${MODELS_MINIO_ACCESS_KEY} --from-literal=MINIO_ROOT_PASSWORD=${MODELS_MINIO_SECRET_KEY}
```

How to create:

```shell
cat env_vars.sh file_with_shell_above.sh | bash
```
!!!! env_vars file has a dependecy on keycloak database.

### Microservices from Images

If you have access to ECR

```shell
IMAGES="annotation:0.1.5-f888d959 \
assets:0.1.7-f888d959 \
convert:0.1.0-4068534a \
jobs:0.1.9-8eec77d8 \
models:0.1.3-cae49287 \
pipelines:0.1.4-dab7a2ea \
processing:0.1.1-f0e8c392 \
scheduler:0.1.1-0ad86fa3 \
search:0.1.4-f888d959 \
users:0.1.2-71a0f115"

for image in $IMAGES; do  
service=$(echo $image | cut -f1 -d':'); 
tag=$(echo $image | cut -f2 -d':');  
helm upgrade -n app -i --set image.tag=${tag} --version ${tag}  ${service}  ${service}/chart/; 
done

helm upgrade -n app -i --set image.tag=0.2.0-5f57ad1c --version 0.2.0-5f57ad1c  badgerdoc-ui  web/chart/; 
```


### How to build images

First you need python base image

```shell
cd infra/docker/python_base
export image_name='artifactory.epam.com:6144/badgerdoc/python_base:0.1.7'
make build
docker tag artifactory.epam.com:6144/badgerdoc/python_base:0.1.7 ${YOUR_IMAGE_NAME}
docker push ${YOUR_IMAGE_NAME}
```

Try to build annotation service and deploy

```shell
cd annotation
export image_name="${YOUR_DOCKER_REGISTRY}/badgerdoc/annotation:0.1.5-${SOME_HASH}"
make build
docker push "${YOUR_DOCKER_REGISTRY}/badgerdoc/annotation:0.1.5-${SOME_HASH}"

#The next step is to deploy chart with new image
helm upgrade -n app -i --set image.tag=0.1.5-${SOME_HASH} --version 0.1.5-${SOME_HASH}  annotation  annotation/chart/ 
```

### How to build all images

```shell
cd infra/docker/python_base
export REGISTRY="badgerdoc"
export image_name="${REGISTRY}/python_base:0.1.7"
make build
cd

SERVICES="assets \
jobs \
pipelines \
search \
annotation \
processing \
models \
users \
convert \
scheduler"

apphostname="app.example.com"

for svc in $SERVICES; do \
cd ${svc}; \
version=$(cat ${svc}/version.txt)
sha=$(git rev-parse --short HEAD)
tag="${version}-${sha}"
image="${REGISTRY}/${svc}:${version}-${sha}"
docker build --target build -t "${image}" . --build-arg "base_image=${image_name}"; \
# docker push "${image}" && helm upgrade -n app -i --set image.registry=${YOUR_REGISTRY},app.hostname=${apphostname},image.tag=${tag} --version ${tag}  ${service}  ${service}/chart/
cd ..; done

```

How to build UI

```shell
export REGISTRY="badgerdoc"
version=$(cat ./version.txt)
sha=$(git rev-parse --short HEAD)
tag="${version}-${sha}"
image="${REGISTRY}/${svc}:${version}-${sha}"
DOCKERFILE="./web/deploy/web.Dockerfile"

cp -r .git ./web/
docker build -t ${image} --no-cache=true --pull --file $DOCKERFILE ./web
# docker push "${image}" && helm upgrade -n app -i --set image.registry=${YOUR_REGISTRY},image.tag=${version} badgerdoc-ui-dev chart/.
rm -rf ./web/.git
```