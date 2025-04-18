import datetime
from typing import Any, Generator

import pytest

import jobs.schemas as schemas


@pytest.fixture(params=[["request_cat"], []])
def categories_change_request(request: Any) -> schemas.JobParamsToChange:
    return schemas.JobParamsToChange(categories=request.param)


@pytest.fixture(params=[["change_cat"], []])
def categories_append_request(request: Any) -> schemas.JobParamsToChange:
    return schemas.JobParamsToChange(categories_append=request.param)


@pytest.fixture()
def mock_ExtractionJobParams():
    mockExtractionJobParams = schemas.ExtractionJobParams(
        name="MockExtractionJobParams",
        files=[1, 2],
        datasets=[1, 2],
        pipeline_name="MockPipeline",
    )
    return mockExtractionJobParams


@pytest.fixture
def mock_AnnotationJobParams():
    mockAnnotationJobParams = schemas.AnnotationJobParams(
        name="MockAnnotationJob",
        datasets=[1, 2],
        files=[1, 2],
        annotators=["annotator1", "annotator2"],
        validators=["validator1", "validator2"],
        owners=["owner1"],
        categories=["category1", "category2"],
        validation_type="cross",
        is_auto_distribution=False,
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    return mockAnnotationJobParams


@pytest.fixture
def mock_AnnotationJobParams2():
    mockAnnotationJobParams2 = schemas.AnnotationJobParams(
        name="MockAnnotationJob",
        datasets=[1, 2],
        files=[1, 2],
        annotators=["annotator1", "annotator2"],
        validators=["validator1", "validator2"],
        owners=["owner2"],
        categories=["category1", "category2"],
        validation_type="cross",
        is_auto_distribution=False,
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    return mockAnnotationJobParams2



@pytest.fixture
def mock_extraction_annotation_job_params() -> Generator[schemas.ExtractionWithAnnotationJobParams, None, None]:
    yield schemas.ExtractionWithAnnotationJobParams(
        name="MockExtractionWithAnnotationJob",
        files=[1, 2],
        datasets=[1, 2],
        pipeline_name="1",
        pipeline_engine="Airflow",
        annotators=["annotator1", "annotator2"],
        validators=["validator1", "validator2"],
        owners=["owner1"],
        categories=["category1", "category2"],
        is_auto_distribution=False,
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=1),
        validation_type="cross",
    )
