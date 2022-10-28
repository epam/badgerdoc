BUILD_TAG=v1.0
TEST_TAG=test1.0
REGISTRY_ADDRESS=localhost:5000
SHELL:=/bin/bash
SONAR_TEST_IMAGE=sonar_test_image
SONAR_TEST_TAG=sonar_test_tag
TEST_IMAGE=test_image
TEST_TAG=test_tag

SHELL:=/bin/bash

.PHONY: build,test

build: Dockerfile
	docker build --target build -t ${image_name} .

test:
	docker build --target test -t ${TEST_IMAGE}:${TEST_TAG} .

sonar_test:
	docker build --target sonar \
	-t ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG} .

	docker run -e SONAR_PROJECT_KEY_MODELS=${SONAR_PROJECT_KEY_MODELS} \
	-e SONAR_HOST_URL=${SONAR_HOST_URL} -e SONAR_TOKEN_MODELS=${SONAR_TOKEN_MODELS} \
	-d ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG}
