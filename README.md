# What is BadgerDoc

**BadgerDoc** is a ML Delivery Platform made to make delivery process of Machine Learning Solutions visible to customer,
managers and ML team. The primary goal of the platform is to visualize ML model delivery cycle -  data annotation, 
model training and result visualization.

The platform has rich functionality in access and data management, annotation setups, and pipeline composition.
Access management is based on Keycloak, which is integrated with Active Directory.
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

## Building the base image

Run the following command to build the base image:

```
make build_base
```

After the base image is built, it is recommended to clean up any temporary files generated during the build process. To do this, run the following command:

```
make clean
```

## Building microservices

Easiest way to build microservices is to run `make build_all` command, right after that, 
it's possible run docker-compose to serve BadgerDoc in local mode.

If it's required to build separate microservice, just run `make build_{microservice}` command,
for instance: `make build_users` to build or rebuild users

## Running BadgerDoc in local mode

After all services are built, you need to create `.env` file in root folder. You may just copy from example: `cp .env.example .env` 

Time to run: 

```
docker-compose -f docker-compose-dev.yaml up -d
```

Now services are running, but to start using BadgerDoc, some additional configuration steps are required

## Keycloak local configuration
_It's a good idea to automate this section_

Important! This is not secure configuration, follow [KeyCloak best practices](https://www.keycloak.org/server/configuration-production) to setup on production environment

1. Login into Keycloak using url http://127.0.0.1:8082/auth and `admin:admin` as credentials

2. Go to Realm Settings -> Keys and disable `RSA-OAEP` algorithm. It will help to avoid issue explainded here https://github.com/jpadilla/pyjwt/issues/722

3. Add tenant attribute to `admin` user, go to Users -> select `admin` -> go to Attributes -> create attribute `tenants:local`, and save

4. Go to Clients -> admin-cli -> Mappers -> Create and fill form with following values:

| Param                      | Value          |
|----------------------------|----------------|
| Protocol                   | openid-connect |
| Name                       | tenants        |
| Mapper Type                | User Attribute |
| User Attribute             | tenants        |
| Token Claim Name           | tenants        |
| Claim JSON Type            | string         |
| Add to ID token            | On             |
| Add to access token        | On             |
| Add to userinfo            | On             |
| Multivalued                | On             |
| Aggregate attribute values | On             |

5. Go to Client Scopes -> Find `roles` and select in list -> Scope -> Add `admin` to Assigned Roles, then go to Mappers and ensure that only 2 mappers exists: `realm roles` and `client roles`. Delete all other mappers

6. Go to Clients -> Create -> Fill form and save

| Param                      | Value              |
|----------------------------|--------------------|
| Client ID                  | badgerdoc-internal |
| Client Protocol            | openid-connect     |

7. Go to Cliens -> Find `badgerdoc-internal` -> change settings `Access Type: Confidential`, set `Service Accounts Enabled` to `On`, add 'Valid Redirect URIs' as '*', then save. Now you can Credentials tab, open it and copy Secret

Now `Client ID` and `Secret` must be set to `.env` as `KEYCLOAK_SYSTEM_USER_CLIENT` and `KEYCLOAK_SYSTEM_USER_SECRET`

8. Go to Clients -> Find `badgerdoc-internal` -> Service Account Roles -> Client Roles -> master-realm -> Find `view-users` and `view-identity-providers` in Available Roles and add to Assigned Roles

9. Go to Roles -> add roles: presenter, manager, role-annotator, annotator, engineer. Open admin role, go to Composite Roles -> Realm Roles and add all these roles 

10. Go to Clients -> badgerdoc-internal and set "Valid Redirect URIs" = * and "Web Origins" = *

Time to reload `docker-compose`, because `.env` was changed: 

```
docker-compose -f docker-compose-dev.yaml up -d
```

## Set up Airflow as a pipeline service in local mode

Airflow runs using its own resources (PostgreSQL, Redis, Flower) without sharing them with BadgerDoc.

1. After setting up BadgerDoc in local mode, run:
```
docker-compose -f airflow/docker-compose-dev.yaml up -d
```
This docker-compose file was downloaded from the Apache Airflow website:
https://airflow.apache.org/docs/apache-airflow/2.7.0/docker-compose.yaml with only a few modifications added.


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

- [Iogsotot](https://github.com/Iogsotot)
- [spiridonovfed](https://github.com/spiridonovfed)
- [nanbratan](https://github.com/nanbratan)
- [sbilevich](https://github.com/sbilevich)
- [serereg](https://github.com/serereg)
- [cakeinsauce](https://github.com/cakeinsauce)
- [Andrka](https://github.com/Andrka)
- [thinklab](https://github.com/thinklab)
- [MagicTearsAsunder](https://github.com/MagicTearsAsunder)
- [Aleksei-Egorenko-EPAM](https://github.com/Aleksei-Egorenko-EPAM)
- [Tokhirov-Abzal](https://github.com/Tokhirov-Abzal)
- [iurii-topychkanov](https://github.com/iurii-topychkanov)
- [khyurri](https://github.com/khyurri)
- [mikemalkhasyanvertex](https://github.com/mikemalkhasyanvertex)
- [andrei-shulaev](https://github.com/andrei-shulaev)
- [Ziprion](https://github.com/Ziprion)
- [AnastasiiaPlyako](https://github.com/AnastasiiaPlyako)
- [gi6rgi](https://github.com/gi6rgi)
- [AbdulAzizi](https://github.com/AbdulAzizi)
- [borisevich-a-v](https://github.com/borisevich-a-v)
- [andgineer](https://github.com/andgineer)
- [cm-howard](https://github.com/cm-howard)
- [Jesovile](https://github.com/Jesovile)
- [Kitonick79](https://github.com/Kitonick79)
- [MysterionRise](https://github.com/MysterionRise)
- [Nathicanaa](https://github.com/Nathicanaa)
- [minev-dev](https://github.com/minev-dev)
- [sokolmask](https://github.com/sokolmask)
- [theoriginmm](https://github.com/theoriginmm)