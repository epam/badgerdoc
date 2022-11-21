### Prerequisites

Before you continue, ensure you have installed the latest versions of Python and pip on your computer. Also you have to install [Docker](https://www.docker.com/) and [Docker-Compose](https://docs.docker.com/compose/).

This project uses [Poetry](https://python-poetry.org/) for dependency and virtual environment management, you also need to install it.

### Dev tools

1) For managing pre-commit hooks this project uses [pre-commit](https://pre-commit.com/).

2) For import sorting this project uses [isort](https://pycqa.github.io/isort/).

3) For code format checking this project uses [black](https://github.com/psf/black).

4) For code linting this project uses [flake8](https://flake8.pycqa.org/en/latest/).

5) For create commits and lint commit messages this project uses [commitizen](https://commitizen-tools.github.io/commitizen/). Instead of 'git commit' run in your terminal to commit staged files:

`make commit`

### Installation

1) Clone the repo:

`git clone https://git.epam.com/epm-uii/badgerdoc/back-end.git`

2) To install the required dependencies and set up a virtual environment run in the cloned directory:

`poetry install`

3) To config pre-commit hooks for code linting, code format checking and linting commit messages run in the cloned directory:

`poetry run pre-commit install`

### Run Docker containers

1) If you did not download Docker base image specified in Dockerfile before, make sure to connect EPAM VPN via `globalprotect` 
and after that login to EPAM artifactory. 
You must connect artifactory using credentials (username and password) provided by DevOps team member or ask your teamlead to help with such request.

*Note: you may find connection URL in Dockerfile FROM instruction ('host:port' part of Docker image path). E.g.:*
```
docker login -u {your username} -p {your password} artifactory.epam.com:6144
```

2) Build app image using

`docker build --target build -t annotation .` or `make image-build`

3) Run Docker containers using

`docker-compose up -d` or `make up`

4) Stop Docker containers using

`docker-compose down` or `make down`

### Documentation

Description of all project's endpoints and API may be viewed without running any services from documentation/openapi.yaml file

To update openapi.yaml after any changes altering the docs, use `make update_docs`

### Technical notes

1) Database migration.

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations. If you are running the database migration manually, you may need to temporarily change the POSTGRES_HOST in .env from `postgres-postgresql` to the database host (for example, `localhost`).


2) Makefile usage

Many useful commands for project are listed in Makefile. To run command just type ``make {command_name}`` in terminal window. 
If your OS doesn't support `make` interface you can run any command from Makefile directly.

3) Hot reload in docker-compose

FastAPI provides feature named [hot-reload](https://fastapi.tiangolo.com/tutorial/first-steps/?h=reload#first-steps). It watches for changes in code
and automatically applies them without the need for a manual restart.  
To make it work in docker-compose
* If you are using Linux, run makefile command `make build-dev-linux`
* If you are using Windows, run makefile command `make build-dev-windows`
* Start docker containers via command `make up`  

Now there is no need to rebuild app image every time you make changes in code.  
It applies to whole `annotation` package, thus changes in `app`, `tests`, `.env`,
`README.md`, etc. will be applied too.  
Also, with hot-reload, you can run tests inside docker container
using command `make docker_test`

4) Running tests.

Project tests are divided in 2 major groups: 
* unit-tests that may successfully run without external dependencies (e.g. without running Docker containers with postgres, minio, etc.);
* integration tests that may successfully run only with some external dependencies (Docker containers).

Some tests also show coverage report. To run each group of tests use `all_test`, `unit_tests` or `integration_tests` commands from Makefile

To run tests inside docker
* If you are using Linux, run makefile command `make test`
* If you are using Windows, run makefile command `make test-windows`
* To run tests inside docker container, check paragraph **Hot reload in docker-compose**

5) To run app locally without building Docker image use `uvicorn app.main:app --host 127.0.0.1 --port 8080`


6) Project may need some dependencies from artifactory base image specified in Dockerfile.  

To run app locally you should install such dependencies from `back-end/python_base/` repo directory via `pip`  
Dependencies should be installed from `back-end` dir  
There are two libraries for local development, that should be installed:
* [filter_lib](https://git.epam.com/epm-uii/badgerdoc/back-end/-/tree/master/python_base/filter_lib) `pip install python_base/filter_lib`
* [tenant_dependency](https://git.epam.com/epm-uii/badgerdoc/back-end/-/tree/master/python_base/tenant_dependency) `pip install python_base/tenant_dependency`

7) Authorization   

With `tenant_dependency` [lib](https://git.epam.com/epm-uii/badgerdoc/back-end/-/tree/master/python_base/tenant_dependency) authorization in SWAGGER is required.  

There are two ways for local development:  
1) Disabling authorization (more convenient way for development)  
2) Authorizing in SWAGGER (better to check, that authorization is working before pushing to repo)  

**Disabling authorization**  

To disable authorization, FastAPI dependency needs to be overrided  
To do that, you need to `export ANNOTATION_NO_AUTH=True` and than rerun uvicorn

**Authorizing in SWAGGER**  

To authorize, you need to:
* Connect to EPAM VPN `GlobalProtect`
* Get token from [auth service](http://dev1.badgerdoc.com/api/v1/users/docs#/auth/login_token_post)  

Params for fields are:
* `grant_type=<some_type>`
* `username=<some_username>`
* `password=<some_username>`
* `client_id=<some_client_id>`  
*NOTE: Ask team member or devops team for authorization parameters*

Other fields may be empty. 
* Click execute
* Copy `access_token` from response body
* Go to SWAGGER
* Click authorize on the top right
* Paste token
* Click `authorize`

For local development `url` in module `/app/token_dependency.py` should be changed
to `http://dev1.badgerdoc.com` or `http://dev2.badgerdoc.com`  
For stands `url` should be `http://bagerdoc-keycloack`

8) Connecting to db on stands (dev1 and dev2)  
* First, you need to connect to EPAM VPN via `globalprotect`  
* Open your db utility (pgadmin, adminer, db utility from PyCharm PRO, etc.)  
* Ask team member or devops team for login and password
* Add new db and provide following creds:
  * dev1
    * host 18.198.231.88
    * port 31240
    * login <postgres_user>
    * pass <postgres_password>
  * dev2
    * host 18.198.231.88
    * port 31995
    * login <postgres_user>
    * pass <postgres_password>

Example of connecting to db will be shown on db utility, that comes with
PyCharm PRO, but there shouldn't be much difference between utilities
   1) Click on the top right `database`
   2) Click on `plus` (on the left)
   3) Click `DataSource`
   4) Click `PostgreSQL`
   5) Enter credentials
