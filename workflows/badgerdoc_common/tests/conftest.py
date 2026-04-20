import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    env_vars = {
        "BADGERDOC_REST_API_RETRY_POLICY": os.getenv(
            "BADGERDOC_REST_API_RETRY_POLICY", "1,2.0,30,3"
        ),
        "TEMPORAL_BADGERDOC_ADDRESS": os.getenv(
            "TEMPORAL_BADGERDOC_ADDRESS", "http://test:8000"
        ),
        "BADGERDOC_TOKEN": os.getenv("BADGERDOC_TOKEN", "test_token"),
        "TEMPORAL_ADDRESS": os.getenv("TEMPORAL_ADDRESS", "localhost:7233"),
        "BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT": os.getenv(
            "BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT", "5"
        ),
    }

    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

    yield

    for key in env_vars.keys():
        if key not in os.environ:
            os.environ.pop(key, None)
