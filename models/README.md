# MODELS

- Start minikube with such or other parameters:

```sh
minikube start --cpus 4 --memory 8192 --insecure-registry="0.0.0.0/0" --kubernetes-version=v1.21.2
```

- Install ambassador

```sh
helm repo add datawire https://getambassador.io
helm repo update
kubectl create ns ambassador
kubectl apply -f https://www.getambassador.io/yaml/aes-crds.yaml
helm install ambassador datawire/ambassador -n ambassador
```

- Install Istio and Knative. You can use this commands from the directory
where istio-minimal-operator.yaml is located:

```sh
curl -sL https://istio.io/downloadIstioctl | sh -
export PATH=$PATH:$HOME/.istioctl/bin
istioctl install -f istio-minimal-operator.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/v0.24.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/v0.24.0/serving-core.yaml
kubectl apply -f https://github.com/knative/net-istio/releases/download/v0.24.0/net-istio.yaml
kubectl label namespace default istio-injection=enabled --overwrite
```
- Create namespace which you will use to deploy models, minio and postgres in.
In this example namespace is "dev2" so it will be "dev2" in yamls below too

```sh
kubectl create ns dev2
kubectl label namespace dev2 istio-injection=enabled --overwrite
```

- Run commands to apply MinIO, PostgreSQL, Models but before doing that
check and modify variables in the next yaml-files, set correct namespace for minio, postgres, rbac:

```sh
kubectl apply -f minio_pvc.yaml
kubectl apply -f minio_deployment.yaml
kubectl apply -f minio_service.yaml
kubectl apply -f postgres_secret.yaml
kubectl apply -f postgres_deployment.yaml
kubectl apply -f postgres_service.yaml
kubectl apply -f rbac_role.yaml
kubectl apply -f rbac_serviceaccount.yaml
kubectl apply -f rbac_rolebinding.yaml
kubectl apply -f log_viewer_role.yaml
kubectl apply -f log_viewer_rolebinding.yaml
```

- Build image for  models and push it to registry

```sh
docker build . --target build -t localhost:5000/models:v1.0
docker push localhost:5000/models:v1.0
```

- Modify variables in the next yamls and apply them

```sh
kubectl apply -f models_deployment.yaml
kubectl apply -f models_service.yaml
```

- You should port-forward minio service and models-service to interact with them:

```sh
kubectl port-forward svc/minio 9001:9001 -n dev2
kubectl port-forward svc/models 8888:80 -n dev2
```

- Now you can deploy model with UI if you have info about model in model_ui database
and checkpoint with config for that model in MinIO. After deploy run this command:

```sh
minikube tunnel
```

- Now your model is available to predict:

```sh
SERVICE_HOSTNAME=$(kubectl get ksvc $MODEL_NAME -n $NAMESPACE -o jsonpath='{.status.url}' | cut -d "/" -f 3)
INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].port}')
INGRESS_HOST=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -v -H "content-type: application/json" -H "Host: ${SERVICE_HOSTNAME}" http://${INGRESS_HOST}:${INGRESS_PORT}/v1/models/${MODEL_NAME}
```
