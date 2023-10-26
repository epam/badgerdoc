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

`git clone `git clone https://git.epam.com/epm-uii/badgerdoc/back-end.git``

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

`docker build --target build -t search .`

3) Run Docker containers using

`docker-compose up -d`

4) Stop Docker containers using

`docker-compose down`

### Documentation

Description of all project's endpoints and API may be viewed without running any services from documentation/openapi.yaml file

### Technical notes

1) Using elasticsearch text analyzer.

For search purpose this app uses the standart elasticsearch text analyzer. It provides grammar based tokenization and works well for most languages. To improve search quality for a specific language it recommended to use specific language analyzer.
To be able to access elasticsearch manually you may need to temporarily change the ES_HOST in .env from "elasticsearch" to the elasticsearch host (for example, "localhost").

2) Support for hierarchical structure of labels.

When an object is indexed, the label field is parsed for nested parts.
When "\_" (underscore) is included in the label value, the object will additionally be associated with the value to the left of the "\_" sign. This is implemented to be able to search for related groups of labels (such as table and part of table, image and part of image).

For example: when indexing the label "foo_bar", the object will be searchable by the values of the label "foo_bar" and "foo".


3) Using minio files storage.

To be able to upload files from S3 storage, user must provide following credentials:
* S3_ENDPOINT_URL - Endpoint url;
* S3_LOGIN - Aws access key id (for minIO it will be login);
* S3_PASS - Aws secret access key (for minIO it will be password);
* S3_START_PATH - annotation servise start path in mionio (i.e. "annotation").

To access minio manually you may need to temporarily change the S3_ENDPOINT_URL in .env to the actual minio host (for example, "http://localhost:{port_number}").


4) Makefile usage

Many useful commands for project are listed in Makefile. To run command just type ``make {command_name}`` in terminal window. 
If your OS doesn't support `make` interface you can run any command from Makefile directly.

5) Hot reload in docker-compose

FastAPI provides feature named [hot-reload](https://fastapi.tiangolo.com/tutorial/first-steps/?h=reload#first-steps). It watches for changes in code
and automatically applies them without the need for a manual restart.  
To make it work in docker-compose
* If you are using Linux, run makefile command `make build-dev-linux`
* If you are using Windows, run makefile command `make build-dev-windows`
* Start docker containers via command `make up`  

Now there is no need to rebuild app image every time you make changes in code.

6) Running tests.

Project tests are divided in 2 major groups: 
* unit-tests that may successfully run without external dependencies (e.g. without running Docker containers with minio, elasticsearch, etc.);
* integration tests that may successfully run only with some external dependencies (Docker containers).

Some tests also show coverage report. To run each group of tests use `all_test`, `unit_tests` or `integration_tests` commands from Makefile

To run tests inside docker
* If you are using Linux, run makefile command `make test`
* If you are using Windows, run makefile command `make test-windows`


7) To run app locally without building Docker image use `uvicorn app.main:app --host 127.0.0.1 --port 8080`


8) Project may need some dependencies from artifactory base image specified in Dockerfile.  

To run app locally you should install such dependencies from `back-end/python_base/` repo directory via `pip`  
Dependencies should be installed from `back-end` dir  
There are two libraries for local development, that should be installed:
* [filter_lib](https://git.epam.com/epm-uii/badgerdoc/back-end/-/tree/master/python_base/filter_lib) `pip install python_base/filter_lib`
* [tenant_dependency](https://git.epam.com/epm-uii/badgerdoc/back-end/-/tree/master/python_base/tenant_dependency) `pip install python_base/tenant_dependency`

9) Authorization   

With `tenant_dependency` [lib](https://git.epam.com/epm-uii/badgerdoc/back-end/-/tree/master/python_base/tenant_dependency) authorization in SWAGGER is required.  

There are two ways for local development:  
1. Disabling authorization (more convenient way for development)  
2. Authorizing in SWAGGER (better to check, that authorization is working before pushing to repo)  

**Disabling authorization**  

To disable authorization, FastAPI dependency needs to be overrided  
To do that, you need to 
- Change `main.py` module to
```python
from tenant_dependency import TenantData

TOKEN = lambda: TenantData(
    token="TEST_TOKEN", user_id="UUID", roles=["role"], tenants=["TEST_TENANT"]
)
```
- After you finish development, do not forget to roll back changes you made to this module  

NOTE: for now this method is working only if you run app locally (not in docker-container)

**Authorizing in SWAGGER**  

To authorize, you need to:
* Connect to EPAM VPN `GlobalProtect`
* Get token from [auth service](http://dev1.gcov.ru/api/v1/users/docs#/auth/login_token_post)  

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
to `http://dev1.gcov.ru` or `http://dev2.gcov.ru`  
For stands `url` should be `http://bagerdoc-keycloack`

10) To test the communication of `annotation` and `search` services locally you may use specific `.env` and `docker-compose.yml` files from the `annotation_search_integration` directory.
    - To run all `annotation` and `search` service's containers within one docker network use `make` command within 'search/' directory (or run an appropriate command from Makefile in terminal directly)
`make annotation_search_integration_up`

    - To stop and remove containers use:
`make annotation_search_integration_down`

    *Note: for integration build, `search` service's app container exposes different port to avoid conflicts with `annotation` service app.*
