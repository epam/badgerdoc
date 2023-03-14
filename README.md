**BadgerDoc** is a ML Delivery Platform made to make delivery process of Machine Learning Solutions visible to customer,
managers and ML team. The primary goal of the platform is to visualize ML model delivery cycle -  data annotation, 
model training and result visualization.

The platform has rich functionality in access and data management, annotation setups, and pipeline composition.
Access management is based on Keycloak, which is integrated with EPAM Active Directory.
Data can be uploaded in batches, organized into datasets as well as uploaded as a single file.
ML pipeline can be applied to a dataset, which will trigger batch processing, or to a single document.
BadgerDoc is capable of annotating large datasets by many annotators. It has algorithms for task distribution,
validation roles, several validation setups and will have multicoverage of files by annotators in nearest future.

BadgerDoc also has steady growing number of pre-trained models available for users, which can be assembled into pipelines through visual editor. 

Having such a rich functionality, BadgerDoc can be used for implementing full ML development cycle,
as well as for rapid prototyping, demonstrating EPAM expertise in ML and even for large annotation
project when preliminary annoation is available. 

For now, BadgerDoc is working with vectorized and scanned documents, but it has capability of image annotation.

#
# Local Setup
## How to build a base Docker image:

1. Copy folders with required dependencies to the base image folder:
```
cp -r lib/filter_lib lib/tenants infra/docker/python_base/
```
2. Rename "tenant" folder:
```
mv infra/docker/python_base/tenants infra/docker/python_base/tenant_dependency
```
3. Open the base Docker image using your favourive text editor:
```
vim infra/docker/python_base/Dockerfile
```
4. Find the following lines and remove them for each dependency install to avoid linting errors:
```
&& black src --check && mypy src && pylint src \
```
5. Build the image, specifying the tag that is used in other Docker images as a "base" image:
```
docker build infra/docker/python_base -t 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
```
P.S. You can get this tag from any microservice Dockerfile like ```processing/Dockerfile```

#
## How to install required dependencies locally

1. Install all required dependencies for a microservice using a packaging tool like Pipenv/Poetry depending on the microservice you are about to set up (we will use Pipenv and "assets" service for this example):
```
cd assets && pipenv install --dev
```
2. Install dependencies from "lib" folder:
```
pipenv shell && pip install -e ../lib/filter_lib ../lib/tenants
```

## Contributors

- [spiridonovfed](@spiridonovfed)
- [Iogsotot](@Iogsotot)
- [sbilevich](@sbilevich)
- [thinklab](@thinklab)
- [MagicTearsAsunder](@MagicTearsAsunder)
- [cakeinsauce](@cakeinsauce)
- [Aleksei-Egorenko-EPAM](@Aleksei-Egorenko-EPAM)
- [iurii-topychkanov](@iurii-topychkanov)
- [andrei-shulaev](@andrei-shulaev)
- [nanbratan](@nanbratan)
- [Ziprion](@Ziprion)
- [khyurri](@khyurri)
- [serereg](@serereg)
- [AnastasiiaPlyako](@AnastasiiaPlyako)
- [Andrka](@Andrka)
- [gi6rgi](@gi6rgi)
- [borisevich-a-v](@borisevich-a-v)
- [andgineer](@andgineer)
- [cm-howard](@cm-howard)
- [Jesovile](@Jesovile)
- [Kitonick79](@Kitonick79)
- [Nathicanaa](@Nathicanaa)
- [minev-dev](@minev-dev)
- [theoriginmm](@theoriginmm)