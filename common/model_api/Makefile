#!/bin/make -f
IMAGE_NAME=common
BUILD_TAG=v1.0
TEST_TAG=test1.0
EXAMPLE_TAG=example

SHELL:=/bin/bash

.PHONY: build,example,test

build: Dockerfile
	docker build --target build -t ${IMAGE_NAME}:${BUILD_TAG} --build-arg ARTIFACTORY_USER=$ARTIFACTORY_USER --build-arg ARTIFACTORY_PASS=$ARTIFACTORY_PASS .

test:
	docker build --target test -t ${IMAGE_NAME}:${TEST_TAG} .

example:
	docker build --target example -t ${IMAGE_NAME}:${EXAMPLE_TAG} .
