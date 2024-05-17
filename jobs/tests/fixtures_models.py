from typing import Any

import pytest

import jobs.models as models


@pytest.fixture(params=[{"categories": ["existing_cat"]}, {"categories": []}])
def combined_job_for_update(request: Any) -> models.CombinedJob:
    job = models.CombinedJob()
    for field, value in request.param.items():
        setattr(job, field, value)
    return job
