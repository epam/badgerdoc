TEST_IMAGE=test
TEST_TAG=test

symlinks:
	rm -rf filter_lib tenant_dependency badgerdoc_cli
	cp -r ../../../lib/filter_lib ./filter_lib
	cp -r ../../../lib/tenants ./tenant_dependency
	cp -r ../../../lib/badgerdoc_cli ./badgerdoc_cli

build: symlinks
	docker build --target build -t ${image_name} .
test: symlinks
	docker build --target test -t ${TEST_IMAGE}:${TEST_TAG} .
