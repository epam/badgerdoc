# What is BadgerDoc

**BadgerDoc** is a platform designed to help show how Machine Learning solutions are delivered to customers, managers, and ML teams. Its main aim is to visualize the process of delivering ML models, including data annotation, model training, and result display.

The platform offers a range of features for managing access and data, setting up annotations, and creating pipelines. Access is managed using Keycloak, which is linked with Active Directory. Data can be uploaded in batches or as individual files, and organized into datasets. ML pipelines can be applied to datasets for batch processing, or to single documents.

BadgerDoc is capable of handling large datasets with annotations from multiple annotators. It includes tools for distributing tasks, validating annotations, and managing multiple annotators. It also provides a growing library of pre-trained models that users can combine using a visual editor.

With its diverse functionality, BadgerDoc can support the entire ML development cycle, rapid prototyping, and showcasing ML expertise. It can also be used for large annotation projects when some initial annotation is already available.

Currently, BadgerDoc primarily works with vectorized and scanned documents but also supports image annotation.
# Local Setup

## Using podman instead of docker
In case you're using Podman, set the `_DOCKER_`` environment variable before proceeding with the next steps:

```
export _DOCKER_=podman
```

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
| -------------------------- | -------------- |
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

5. Go to Client Scopes -> Find `roles` -> Scope and select `admin` in list  to add to Assigned Roles, then go to Mappers and ensure that only 2 mappers exists: `realm roles` and `client roles`. Delete all other mappers

6. Go to Clients -> Create -> Fill form and save

| Param           | Value              |
| --------------- | ------------------ |
| Client ID       | badgerdoc-internal |
| Client Protocol | openid-connect     |

7. Go to Cliens -> Find `badgerdoc-internal` -> change settings `Access Type: Confidential`, set `Service Accounts Enabled` to `On`, set 'Valid Redirect URIs' and 'Web Origins' to '_', then save. Now you can Credentials tab, open it and copy Secret

Then `Client ID` and `Secret` must be set to `.env` as `KEYCLOAK_SYSTEM_USER_CLIENT=badgerdoc-internal` and `KEYCLOAK_SYSTEM_USER_SECRET` to copied key

8. Go to Clients -> Find `badgerdoc-internal` -> Service Account Roles -> Client Roles -> master-realm -> Find `view-users` and `view-identity-providers` in Available Roles and add to Assigned Roles

9. Go to Roles -> add roles: presenter, manager, role-annotator, annotator, engineer. Open admin role, go to Composite Roles -> Realm Roles and add all these roles

10. Go to Realm Settings -> Tokens -> Find `Access Token Lifespan` and set 1 `Days`

Time to reload `docker-compose`, because `.env` was changed:

```
docker-compose -f docker-compose-dev.yaml up -d
```

## Categories

Be sure that you added all possible categories via badgerdoc UI (/categories) otherwise you get undefined categories on annotations view page

## Set up Airflow as a pipeline service in local mode

Airflow runs using its own resources (PostgreSQL, Redis, Flower) without sharing them with BadgerDoc.

1. Copy `airflow/.env.example` to `airflow/.env` running:
```
cp airflow/.env.example airflow/.env
```

To setup service account you need to configure Keycloak for BadgerDoc first.

2. Setup service account. Login into Keycloak using url http://127.0.0.1:8082/auth and `admin:admin` as credentials. Select Clients -> badgerdoc-internal -> Service Accounts Roles -> Find Service Account User and click "service-account-badgerdoc-internal". Then select Attributes tab and add `tenants:local` attribute like you did it for `admin`. 

3. Go to Role Mappings and assign `admin` and `default-roles-master`

4. Go to Clients -> badgerdoc-internal -> Mappers -> Create and fill form: 

| Param                      | Value          |
| -------------------------- | -------------- |
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

5. Copy `KEYCLOAK_SYSTEM_USER_SECRET` from Badgerdoc `.env` file into Airflow `.env` file, then run 

```
docker-compose -f airflow/docker-compose-dev.yaml up -d
```

6. Login to Airflow 

This docker-compose file was downloaded from the Apache Airflow website:
https://airflow.apache.org/docs/apache-airflow/2.7.0/docker-compose.yaml with only a few modifications added.

## Set up ClearML as Models service in local mode

ClearML runs using its own resources without sharing them with BadgerDoc.

1. Copy `clearml/.env.example` to `clearml/.env` running:
```
cp clearml/.env.example clearml/.env
```

2. Run:
```
docker-compose -f clearml/docker-compose-dev.yaml up -d
```

This docker-compose file was downloaded from the ClearML GitHub: https://github.com/allegroai/clearml-server/blob/master/docker/docker-compose.yml with a few modifications added.

## How to install required dependencies locally

1. Install all required dependencies for a microservice using a packaging tool like Pipenv/Poetry depending on the microservice you are about to set up (we will use Pipenv and "assets" service for this example):

```
cd assets && pipenv install --dev
```

2. Install dependencies from "lib" folder:

```
pipenv shell && pip install -e ../lib/filter_lib ../lib/tenants
```

## API docs (swagger)

Use this URL to open the swagger of some service

```
http://127.0.0.1:8080/{service_name}/docs
```

For example: http://127.0.0.1:8080/users/docs

## Contributors

<a href="https://github.com/epam/badgerdoc/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=epam/badgerdoc">
</a>
