#!/bin/make -f
BUILD_TAG=v1.0
TEST_TAG=test1.0
REGISTRY_ADDRESS=localhost:5000
SHELL:=/bin/bash
IMAGE=models
SONAR_TEST_IMAGE="sonar_test_image"
SONAR_TEST_TAG="sonar_test_tag"

.PHONY: build,test

build:
	docker build --target build . -t ${image_name}

build-dev-linux:
	DOCKER_BUILDKIT=1 docker build --target build-dev . -t ${image_name}

build-dev-windows:
	set "DOCKER_BUILDKIT=1" && docker build --target build-dev . -t ${image_name}

buildlocal: Dockerfile
	docker build --target build . -t ${REGISTRY_ADDRESS}/${IMAGE}:${BUILD_TAG}

test:
	docker build --target test . -t ${REGISTRY_ADDRESS}/${IMAGE}:${TEST_TAG}

sonar_test:
	docker build --target sonar \
	-t ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG} .

	docker run -e SONAR_PROJECT_KEY_MODELS=${SONAR_PROJECT_KEY_MODELS} \
	-e SONAR_HOST_URL=${SONAR_HOST_URL} -e SONAR_TOKEN_MODELS=${SONAR_TOKEN_MODELS} \
	-d ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG}

sort:
	poetry run isort --line-length 79 .

refactor:
	poetry run black --line-length 79 .

lint:
	poetry run flake8 .

up:
	docker-compose up -d

down:
	docker-compose down

start:
	docker-compose start

stop:
	docker-compose stop

upgrade:
	poetry run alembic upgrade head

downgrade:
	poetry run alembic downgrade -1

commit:
	poetry run cz commit

run:
	poetry run uvicorn src.main:app --reload
