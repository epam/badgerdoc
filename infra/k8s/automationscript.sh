#!bin/bash
set -ex

# Set the public ip of node that will be used as bastion host and by kubectl
NODE_PUBLIC_IP=3.125.238.128
NODE_PORT=6443

# Check prerequisites
Requirements="git pip3 kubectl helm curl"

for req in $Requirements; do
    if ! command -v $req &> /dev/null; then
        echo "$req not found. Please install $req"
        exit
    else 
        echo "$req OK"
    fi
done


# Configure ssh to connect to baction_doc
# You should put your private key in ~/.ssh/badgerdoc

if grep -q bastion_doc ~/.ssh/config; then
    echo "bastion_doc host already configured"
else
    cat <<EOF >> ~/.ssh/config
Host bastion_doc
    Port 22
    HostName $NODE_PUBLIC_IP
    User centos
    IdentitiesOnly yes
    IdentityFile ~/.ssh/badgerdoc
EOF
    echo "bastion_doc host configured"
fi

# Checks if ssh key exists
if [ -f ~/.ssh/badgerdoc ]; then
    echo "ssh OK"
else 
    echo "No ssh key provided.Please put your private key in ~/.ssh/badgerdoc"
    exit
fi

# Clone badgerdoc_infra_k8s and kubespray repo
git clone https://git.epam.com/epm-uii/badgerdoc/badgerdoc_infra/badgerdoc_infra_k8s.git
git clone https://github.com/kubernetes-sigs/kubespray
cp -r badgerdoc_infra_k8s/kubespray/mycluster kubespray/inventory/


# Install python dependencies and run playbook
# Note that there may be issues with ansible and ansible_core versioning
pip3 install -r kubespray/requirements.txt
ansible-playbook -i kubespray/inventory/mycluster/hosts.yaml  --become --become-user=root kubespray/cluster.yml

# Set kubeconfig to access cluster
cp kubespray/inventory/mycluster/artifacts/admin.conf ~/.kube/admin.conf
sed -i "s|server.*|server: https://$NODE_PUBLIC_IP:$NODE_PORT|" ~/.kube/admin.conf
if [ ! -f ~/.kube/admin.conf ]; then
    echo "admin.conf not found. Please create ~/.kube/admin.conf with credentials"
    exit
fi

export KUBECONFIG=$HOME/.kube/admin.conf
if [[ $(kubectl get ns | wc -l) -gt 5 ]]; then
    echo "We assume that provided KUBECONFIG is not correct"
    echo "Please check if kubectl connects to the expected cluster"
    exit
fi

# Patch csi driver:
kubectl annotate serviceaccount -n kube-system ebs-csi-controller-sa eks.amazonaws.com/role-arn=arn:aws:iam::818863528939:role/badgerdoc-ebs-csi-driver-role

# Patch storageclass:
kubectl patch storageclass ebs-sc -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Install ambassador:
helm repo update
kubectl apply -f badgerdoc_infra_k8s/helm/ambassador/aes-crds.yaml
kubectl create namespace ambassador
helm install ambassador --namespace ambassador datawire/ambassador -f badgerdoc_infra_k8s/helm/ambassador/ambassador.values.yaml
kubectl patch deployment ambassador -n ambassador --patch "$(cat badgerdoc_infra_k8s/helm/ambassador/ambassador.patch.yaml)"
kubectl apply -f badgerdoc_infra_k8s/helm/ambassador/ambassador.host.yaml
kubectl apply -f badgerdoc_infra_k8s/helm/ambassador/ambassador.module.yaml

# Install istio:
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

# Replace istio-ingressgateway with NodePort:
kubectl delete svc istio-ingressgateway -n istio-system
kubectl apply -f badgerdoc_infra_k8s/helm/istio/patched_istio_svc.yaml

# Install knative:
kubectl create ns knative-serving
kubectl apply -f badgerdoc_infra_k8s/knative/operator.yaml
sleep 10
kubectl apply -f badgerdoc_infra_k8s/knative/knative_serving.yaml
kubectl apply -f badgerdoc_infra_k8s/knative/domain.configuration.yaml
kubectl label namespace knative-serving istio-injection=enabled
kubectl label namespace default istio-injection=enabled

# Install minio and postgres:
git clone git@git.epam.com:epm-uii/badgerdoc/badgerdoc_infra/badgerdoc_infra_helm.git
helm repo add bitnami https://charts.bitnami.com/bitnami
kubectl create ns dev1
kubectl create ns dev2
helm install postgres -n dev1 bitnami/postgresql -f badgerdoc_infra_helm/postgres/values.yaml
helm install postgres -n dev2 bitnami/postgresql -f badgerdoc_infra_helm/postgres/values.yaml
helm install --namespace minio-operator --create-namespace --generate-name minio/minio-operator -f badgerdoc_infra_helm/minio/values.yaml

# Install monitoring stack
kubectl apply -f badgerdoc_infra_k8s/helm/monitoring-stack/cm-ambassador-dashnnoard.yaml
helm install -f badgerdoc_infra_k8s/helm/monitoring-stack/monitoring-stack-values.yaml kps prometheus-community/kube-prometheus-stack
kubectl apply -f badgerdoc_infra_k8s/helm/monitoring-stack/ambassador-service-monitor.yaml
helm install -f badgerdoc_infra_k8s/helm/monitoring-stack/vmsingle-values.yaml vm-server vm/victoria-metrics-single
helm install -f badgerdoc_infra_k8s/helm/monitoring-stack/vmalert-values.yaml vm-alert vm/victoria-metrics-alert


# Install latest reelease Metrics-server, --kubelet-insecure-tls is enabled
# ref: https://github.com/kubernetes-sigs/metrics-server

kubectl apply -f badgerdoc_infra_k8s/metrics-server/components.yaml

