import pytest
from fastapi.testclient import TestClient
from tests.override_app_dependency import TEST_HEADERS, app

from annotation.schemas import EntitiesStatusesSchema, TaskStatusEnumSchema

client = TestClient(app)


@pytest.mark.unittest
def test_get_entities_statuses_successful_response():
    expected_result = EntitiesStatusesSchema(
        task_statuses=(status.value for status in TaskStatusEnumSchema)
    )
    expected_status_code = 200

    response = client.get("/metadata", headers=TEST_HEADERS)

    assert response.json() == expected_result
    assert response.status_code == expected_status_code
