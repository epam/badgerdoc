TEST_IMAGE=test
TEST_TAG=test

build:
	docker build --target build -t ${image_name} .
test:
	docker build --target test -t ${TEST_IMAGE}:${TEST_TAG} .
