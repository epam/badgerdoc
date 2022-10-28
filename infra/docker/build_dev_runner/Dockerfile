###################################################
# Creates image for build runner
#
#                        ##         .
#                  ## ## ##        ==
#               ## ## ## ## ##    ===
#           /"""""""""""""""""\___/ ===
#      ~~~ {~~ ~~~~ ~~~ ~~~~ ~~~ ~ /  ===- ~~~
#           \______ o           __/
#             \    \         __/
#              \____\_______/
#
# Author:  Nikolai Volkov <nikolai_volkov@epam.com>
# version: 0.1.2
#
###################################################

ARG TAG=3.14
FROM alpine:$TAG

ARG VERSION=2.34
ARG GLIBC_URL=https://github.com/sgerrand/alpine-pkg-glibc/releases/download/${VERSION}-r0/glibc-${VERSION}-r0.apk
ARG GLIBC_BIN_URL=https://github.com/sgerrand/alpine-pkg-glibc/releases/download/${VERSION}-r0/glibc-bin-${VERSION}-r0.apk
ARG PUB_KEY_URL=https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub
ARG KEY_PATH=/etc/apk/keys/sgerrand.rsa.pub
ARG AWSCLI_URL=https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip

# Install necessary tools, docker and glibc libs
RUN apk --no-cache add ca-certificates bash make git binutils curl wget jq docker \
    && wget -q -O ${KEY_PATH} ${PUB_KEY_URL} \
    && wget ${GLIBC_URL} \
    && wget ${GLIBC_BIN_URL} \
    && apk add --no-cache glibc-${VERSION}-r0.apk glibc-bin-${VERSION}-r0.apk
    
# Install AWS CLI v2
RUN wget -q -O awscliv2.zip ${AWSCLI_URL} \
    && unzip awscliv2.zip \
    && aws/install

# Clean
RUN rm -rf awscliv2.zip aws \
    /usr/local/aws-cli/v2/*/dist/aws_completer \
    /usr/local/aws-cli/v2/*/dist/awscli/data/ac.index \
    /usr/local/aws-cli/v2/*/dist/awscli/examples \
    && apk --no-cache del \
    binutils \
    && rm glibc-${VERSION}-r0.apk \
    && rm glibc-bin-${VERSION}-r0.apk \
    && rm -rf /var/cache/apk/*
