#!/bin/make -f
#BUILD_TAG=v1.0
PUSH_TAG=pypi
#TEST_TAG=test1.0
SHELL:=/bin/bash

.PHONY: build,test

build: Dockerfile
# ${image_name} is base_image name. Look at the core Makefile
	docker build --target build -t ${image_name} .

# "push" is additional container just for push code to pypi artifactory repo
# should be destroyed after clean pipeline stage 
# TODO: job-containers
	docker build --target push -t ${image_name}_${PUSH_TAG} .
	docker run -e ARTIFACTORY_USER=${ARTIFACTORY_USER} -e ARTIFACTORY_PASS=${ARTIFACTORY_PASS} -d ${image_name}_${PUSH_TAG}

test:
	docker build --target test -t ${IMAGE_NAME}:${TEST_TAG} .
