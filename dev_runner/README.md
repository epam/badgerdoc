# Local Dev Runner

This is a subproject for BadgerDoc to run a local development environment.

## How to Use

### Install Python Dependencies
Use poetry to install dependencies:
```bash
 poetry install
```

If you have problems with dependencies, you can try to update them. Initially, install [poetry export plugin](https://pypi.org/project/poetry-plugin-export/).
And then run the following command:
```bash
 ./collect_requirements.sh
```


On Windows and Mac you may need one extra package:
```bash
 pip install python-magic-bin
```
And for Mac additionally:
```bash
 brew install libmagic
```

### External Dependencies
There is a row of external dependencies, to run them you need to use docker-compose:
 ```bash
 docker-compose up
 ```

### Run the BadgerDoc

To run the migration for all services you need to run external dependencies first and then run following command:
```bash
bash ./migration.sh
```

To run the all the services you need to run the following command:
 ```bash
 python start.py
 ```
Or you can run only the services you need (see help for more information):
```bash
python start.py annotation users
 ```