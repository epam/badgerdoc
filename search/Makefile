SONAR_TEST_IMAGE="sonar_test_image"
SONAR_TEST_TAG="sonar_test_tag"

req:
	poetry export -f requirements.txt --output requirements.txt

sort:
	poetry run isort --line-length 79 .

check_sort:
	poetry run isort --line-length 79 . --check

lint:
	poetry run flake8 .

format:
	poetry run black --check --line-length 79 .

refactor:
	poetry run black --line-length 79 .

test_checks: check_sort format lint unit_tests

all_test:
	poetry run pytest --cov-report term --cov=app --cov=harvester tests

unit_tests:
	poetry run pytest --cov-report= --cov=app tests -m unittest

integration_tests:
	poetry run pytest tests -m integration

check: sort refactor lint all_test

commit:
	poetry run cz commit

pre-commit:
	poetry run pre-commit install

run:
	poetry run uvicorn search.main:app --reload

build:
	docker build --target build -t ${image_name} .

test:
	DOCKER_BUILDKIT=1 docker build --target test -t search .

test-windows:
	set "DOCKER_BUILDKIT=1" && docker build --target test -t search .

image-build:
	docker build --target build -t search .

build-dev-linux:
	DOCKER_BUILDKIT=1 docker build --target build-dev -t search .

build-dev-windows:
	set "DOCKER_BUILDKIT=1" && docker build --target build-dev -t search .

image-run:
	docker run -d --name search -p 8080:8080 search

up:
	docker-compose up -d

down:
	docker-compose down

start:
	docker-compose start

stop:
	docker-compose stop

sonar_test:
	docker build --target sonar \
	-t ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG} .
	
	docker run -e SONAR_PROJECT_KEY_SEARCH=${SONAR_PROJECT_KEY_SEARCH} \
	-e SONAR_HOST_URL=${SONAR_HOST_URL} -e SONAR_TOKEN_SEARCH=${SONAR_TOKEN_SEARCH} \
	-d ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG}

annotation_search_integration_up:
	docker-compose --env-file ./annotation_search_integration/.env \
	-f ./annotation_search_integration/docker-compose.yml -p annotation-search up -d --build

annotation_search_integration_down:
	docker-compose --env-file ./annotation_search_integration/.env \
	-f ./annotation_search_integration/docker-compose.yml -p annotation-search down
