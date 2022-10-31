#!/bin/make -f
IMAGE_NAME=post
BUILD_TAG=v1.1
TEST_TAG=test1.1
BUILD_IMAGE=${image_name}
SONAR_TEST_IMAGE="sonar_test_image"
SONAR_TEST_TAG="sonar_test_tag"

SHELL:=/bin/bash

.PHONY: build,test

build: Dockerfile
	docker build --target build -t ${image_name} .
test: tests
	docker build --target test -t ${IMAGE_NAME}:${TEST_TAG} .

sonar_test:
	docker build --target sonar \
	-t ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG} .
	
	docker run -e SONAR_PROJECT_KEY_PROCESSING=${SONAR_PROJECT_KEY_PROCESSING} \
	-e SONAR_HOST_URL=${SONAR_HOST_URL} -e SONAR_TOKEN_PROCESSING=${SONAR_TOKEN_PROCESSING} \
	-d ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG}
