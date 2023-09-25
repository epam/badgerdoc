build_all:  build_base build_annotation build_users build_convert build_jobs build_keycloak build_assets build_web  build_processing build_pipelines build_models build_taxonomy clean

build_base: 
	mkdir -p build_dir
	cp -r lib/ build_dir/lib
	cp infra/docker/python_base/Dockerfile build_dir 
	docker build --target base build_dir/ -t 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7

build_keycloak:
	mkdir -p build_dir
	git clone https://github.com/keycloak/keycloak-containers.git build_dir/keycloak
	cd build_dir/keycloak; git checkout 15.1.1
	docker build build_dir/keycloak/server -t badgerdoc_keycloak

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

build_pipelines:
	docker build --target build pipelines/ -t badgerdoc_pipelines

build_models:
	docker build --target build models/ -t badgerdoc_models

build_taxonomy:
	docker build --target build taxonomy/ -t badgerdoc_taxonomy

clean:
	rm -rf build_dir