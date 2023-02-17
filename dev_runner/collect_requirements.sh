#!/bin/bash

set -e -x

TMP_REQUIREMENTS_FILE=$(mktemp)
ROOT_DIR=$(git rev-parse --show-toplevel)
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
POETRY_SERVICES=(search annotation convert models processing taxonomy)
PIPENV_SERVICES=(assets)
PIP_SERVICES=(jobs pipelines scheduler users)
DUPLICATED_DEPENDENCIES=(starlette fastapi aiohttp sqlalchemy_utils sqlalchemy aiosignal alembic anyio asgiref attrs boto3 botocore cachetools certifi cffi charset-normalizer click colorama cryptography h11 idna importlib-metadata importlib-resources jmespath mako markupsafe pillow psycopg2-binary pycparser pydantic pyjwt python-dotenv pyyaml requests s3transfer setuptools typing-extensions urllib3 uvicorn yarl zipp frozenlist minio multidict sniffio aiokafka websocket-client)

collect_poetry_dependencies() {
    for poetry_service in "${POETRY_SERVICES[@]}"; do
        cd "$ROOT_DIR/$poetry_service" || exit
        # ensure that you have https://pypi.org/project/poetry-plugin-export/ installed
        poetry export -f requirements.txt --without-hashes | cut -d \; -f 1 >> "$TMP_REQUIREMENTS_FILE"
    done
}

collect_pipenv_dependencies() {
    for pipenv_service in "${PIPENV_SERVICES[@]}"; do
        cd "$ROOT_DIR/$pipenv_service" || exit
        pipenv requirements | tail -n +2 | cut -d \; -f 1 >> "$TMP_REQUIREMENTS_FILE"
    done
}

collect_pip_dependencies() {
    for pip_service in "${PIP_SERVICES[@]}"; do
        cd "$ROOT_DIR/$pip_service" || exit
        if [ -f requirements.txt ]; then
            cat requirements.txt | cut -d \; -f 1 >> "$TMP_REQUIREMENTS_FILE"
        fi
    done
}

collect_poetry_dependencies
collect_pipenv_dependencies
collect_pip_dependencies
cd "$SCRIPT_DIR" || exit
requirementes=$(cat "$TMP_REQUIREMENTS_FILE")
for dependency in "${DUPLICATED_DEPENDENCIES[@]}"; do
    requirementes=$(echo "$requirementes" | grep -v "$dependency")
done
echo $requirementes | xargs poetry -v add

for dependency in "${DUPLICATED_DEPENDENCIES[@]}"; do
    poetry add "$dependency"=="*"
done

poetry add ../lib/tenants ../lib/filter_lib python-magic-bin
