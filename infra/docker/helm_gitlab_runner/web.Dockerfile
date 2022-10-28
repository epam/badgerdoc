ARG TAG=3
FROM alpine:$TAG

ARG KUBECTL_VERSION=v1.21.2
ARG KUBECTL_URL=https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl
ARG KUBECTL_PATH=/usr/local/bin/kubectl
ARG HELM_VERSION=v3.6.3
ARG HELM_URL=https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz
ARG HELM_TAR=helm-${HELM_VERSION}-linux-amd64.tar.gz
ARG HELM_PATH=/usr/local/bin
ARG WORK_DIR=/config
ARG HELM_REPO_NAME=stable
ARG HELM_REPO_URL=https://charts.helm.sh/stable

RUN apk add --no-cache ca-certificates bash git openssh curl gettext jq bind-tools make

RUN wget -q ${KUBECTL_URL} -O ${KUBECTL_PATH} \
    && chmod +x ${KUBECTL_PATH} \
    && wget -q ${HELM_URL} -P ${HELM_PATH} \
    && tar -zxf ${HELM_PATH}/${HELM_TAR} -C ${HELM_PATH} \
    && mv ${HELM_PATH}/linux-amd64/helm ${HELM_PATH}/helm \
    && helm repo add ${HELM_REPO_NAME} ${HELM_REPO_URL} --force-update

WORKDIR ${WORK_DIR}

RUN chmod g+rwx /root \
    && chmod g+rwx ${WORK_DIR} \
    && rm -rf ${HELM_PATH}/linux-amd64 \
    && rm ${HELM_PATH}/${HELM_TAR}

CMD bash
