SONAR_TEST_IMAGE="sonar_test_image_taxonomy"
SONAR_TEST_TAG="sonar_test_tag_taxonomy"
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
	poetry run pytest --cov-report term --cov=app tests

unit_tests:
	poetry run pytest --cov-report= --cov=app tests -m unittest

integration_tests:
	poetry run pytest tests -m integration

docker_test:
	docker exec taxonomy pytest --cov-report term --cov=app tests

check: sort refactor lint all_test

commit:
	poetry run cz commit

pre-commit:
	poetry run pre-commit install

run:
	poetry run uvicorn app.main:app --reload

update_docs:
	poetry run python -m documentation.update_docs

build:
	docker build --target build -t ${image_name} .

test:
	DOCKER_BUILDKIT=1 docker build --target test -t taxonomy .

test-windows:
	set "DOCKER_BUILDKIT=1" && docker build --target test -t taxonomy .

sonar_test:
	docker build --target sonar-taxonomy \
	-t ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG} .
	
	docker run -e SONAR_PROJECT_KEY_TAXONOMY=${SONAR_PROJECT_KEY_TAXONOMY} \
	-e SONAR_HOST_URL=${SONAR_HOST_URL} -e SONAR_TOKEN_TAXONOMY=${SONAR_TOKEN_TAXONOMY} \
	-d ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG}

image-build:
	docker build --target build -t taxonomy .

build-dev-linux:
	DOCKER_BUILDKIT=1 docker build --target build-dev -t taxonomy .

build-dev-windows:
	set "DOCKER_BUILDKIT=1" && docker build --target build-dev -t taxonomy .

image-run:
	docker run -d --name taxonomy -p 80:80 taxonomy

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
