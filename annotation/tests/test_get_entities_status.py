import pytest
from fastapi.testclient import TestClient

from annotation.schemas import EntitiesStatusesSchema, TaskStatusEnumSchema
from tests.override_app_dependency import TEST_HEADERS, app

client = TestClient(app)


@pytest.mark.unittest
def test_get_entities_statuses_successful_response():
    expected_result = EntitiesStatusesSchema(
        task_statuses=(status.value for status in TaskStatusEnumSchema)
    )
    expected_status_code = 200

    response = client.get("/metadata", headers=TEST_HEADERS)
    expected_test_statuses = [
        el.value for el in expected_result.model_dump()["task_statuses"]
    ]

    assert response.json()["task_statuses"] == expected_test_statuses
    assert response.status_code == expected_status_code
