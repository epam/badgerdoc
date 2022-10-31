#!/bin/bash
set -x

apk --no-cache add \
binutils \
curl \
&& curl -sL https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.23-r2/sgerrand.rsa.pub -o /etc/apk/keys/sgerrand.rsa.pub \
&& curl -sLO https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.23-r2/glibc-2.23-r2.apk \
&& curl -sLO https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.23-r2/glibc-bin-2.23-r2.apk \
&& apk add --no-cache \
glibc-2.23-r2.apk \
glibc-bin-2.23-r2.apk \
&& curl -sL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip \
&& unzip awscliv2.zip \
&& aws/install \
&& rm -rf \
awscliv2.zip \
aws \
/usr/local/aws-cli/v2/*/dist/aws_completer \
/usr/local/aws-cli/v2/*/dist/awscli/data/ac.index \
/usr/local/aws-cli/v2/*/dist/awscli/examples \
&& apk --no-cache del \
binutils \
curl \
&& rm glibc-2.23-r2.apk \
&& rm glibc-bin-2.23-r2.apk \
&& rm -rf /var/cache/apk/*

