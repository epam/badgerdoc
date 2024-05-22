from unittest.mock import patch

import pytest

from processing.config import settings
from processing.tasks import PreprocessingTask


@pytest.mark.skip
@pytest.fixture(scope="module")
def mock_preprocessing_task():
    task = PreprocessingTask(
        model_id="1",
        file_id=1,
        languages=["1"],
        pages={1},
        tenant="1",
        token="1",
    )
    yield task


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["failed", "in_progress", "preprocessed"])
async def test_send_status_to_assets(mock_preprocessing_task, status):
    with patch("processing.tasks.send_request") as mock:
        await mock_preprocessing_task.send_status_to_assets(status)
        mock.assert_awaited_once_with(
            method="PUT",
            url=settings.assets_url,
            json={
                "file": int(mock_preprocessing_task.file_id),
                "status": status,
            },
            headers={
                "X-Current-Tenant": mock_preprocessing_task.tenant,
                "Authorization": f"Bearer {mock_preprocessing_task.token}",
            },
        )
