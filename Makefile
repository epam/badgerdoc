build_all:  build_base build_annotation build_users build_convert build_jobs build_keycloak build_assets build_web build_processing clean

build_base: 
	mkdir -p build_dir
	cp -r lib/ build_dir/lib
	cp infra/docker/python_base/Dockerfile build_dir 
	docker build --target base build_dir/ -t 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7

mac_docker_config := ~/Library/Group\ Containers/group.com.docker/settings.json
is_rosetta_enabled := $(shell grep -o '"useVirtualizationFrameworkRosetta": *\(true\|false\)' $(mac_docker_config) | awk -F: '{print $$2}' | tr -d ' ')

build_keycloak:
	@echo "Checking architecture..."
	@if [ "$(shell uname -m)" = "arm64" ]; then \
		echo "arm64 architecture detected"; \
		if [ "$(is_rosetta_enabled)" = "false" ]; then \
			echo "Rosetta emulation is not enabled for Docker, using full build for keycloak"; \
			$(MAKE) build_keycloak_full; \
		else \
			echo "Rosetta emulation is enabled for Docker, pulling keycloak image"; \
			$(MAKE) pull_keycloak; \
		fi; \
	else \
		echo "Building for non-arm64 architecture"; \
		$(MAKE) pull_keycloak; \
	fi

pull_keycloak:
	docker pull quay.io/keycloak/keycloak:15.1.1
	docker tag quay.io/keycloak/keycloak:15.1.1 bargerdoc_keycloak

build_keycloak_full:
	mkdir -p build_dir
	git clone https://github.com/keycloak/keycloak-containers.git build_dir/keycloak
	cd build_dir/keycloak; git checkout 15.1.1
	docker build build_dir/keycloak/server -t bargerdoc_keycloak

build_annotation:
	docker build --target build annotation/ -t badgerdoc_annotation

build_users:
	docker build --target build users/ -t badgerdoc_users

build_convert:
	docker build --target build convert/ -t badgerdoc_convert

build_processing:
	docker build --target build processing/ -t badgerdoc_processing

build_jobs:
	docker build --target build jobs/ -t badgerdoc_jobs

build_assets:
	docker build --target build assets/ -t badgerdoc_assets

build_web:
	docker build --target build web/ -t badgerdoc_web

clean : 
	rm -rf build_dir