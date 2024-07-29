_DOCKER_ ?= docker

# Build all microservices
build_all:  build_base build_base_3.12 build_annotation build_users build_convert build_jobs build_keycloak build_assets build_web  build_processing build_taxonomy clean

# Build only BadgerDoc microservices
build_badgerdoc: build_base build_base_3.12 build_annotation build_users build_convert build_jobs build_assets build_web  build_processing build_taxonomy clean

build_base: 
	mkdir -p build_dir
	cp -r lib/ build_dir/lib
	cp infra/docker/python_base/Dockerfile build_dir 
	${_DOCKER_} build --target base build_dir/ -t 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.8

build_base_3.12:
	mkdir -p build_dir_3.12
	cp -r lib/ build_dir_3.12/lib
	cp infra/docker/python_base_3.12/Dockerfile build_dir_3.12
	${_DOCKER_} build --target base build_dir_3.12/ -t 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base_3.12:0.2.0

build_keycloak:
	mkdir -p build_dir
	git clone https://github.com/keycloak/keycloak-containers.git build_dir/keycloak
	cd build_dir/keycloak; git checkout 15.1.1
	${_DOCKER_} build build_dir/keycloak/server -t badgerdoc_keycloak

build_annotation:
	${_DOCKER_} build --target build annotation/ -t badgerdoc_annotation

build_users:
	${_DOCKER_} build --target build users/ -t badgerdoc_users

build_convert:
	${_DOCKER_} build --target build convert/ -t badgerdoc_convert

build_processing:
	${_DOCKER_} build --target build processing/ -t badgerdoc_processing

build_jobs:
	${_DOCKER_} build --target build jobs/ -t badgerdoc_jobs

build_assets:
	${_DOCKER_} build --target build assets/ -t badgerdoc_assets

build_web:
	${_DOCKER_} build --target build web/ -t badgerdoc_web

build_taxonomy:
	${_DOCKER_} build --target build taxonomy/ -t badgerdoc_taxonomy

clean:
	rm -rf build_dir