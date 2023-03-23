build_all:  build_base build_annotation build_users clean

build_base : 
	mkdir build_dir
	cp -r lib/ build_dir/lib
	cp infra/docker/python_base/Dockerfile build_dir 
	docker build --target base build_dir/ -t 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7

build_annotation:
	docker build --target build annotation/ -t badgerdoc_annotation

build_users:
	docker build --target build users/ -t badgerdoc_users

clean : 
	rm -rf build_dir