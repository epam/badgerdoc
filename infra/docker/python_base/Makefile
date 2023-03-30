TEST_IMAGE=test
TEST_TAG=test

symlinks:
	rm -rf filter_lib tenant_dependency
	cp -r ../../../lib/ ./lib/

build: symlinks
	docker build --target base -t ${image_name} .
test: symlinks
	docker build --target test -t ${TEST_IMAGE}:${TEST_TAG} .
