import datetime

import pytest

from jobs.schemas import JobParams, ValidationType


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotation_job_lack_of_data(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
            "is_draft": False,
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "validation_type"],
                "msg": "validation_type cannot be empty for AnnotationJob",
                "type": "value_error",
            },
            {
                "loc": ["body", "owners"],
                "msg": "owners cannot be empty for AnnotationJob",
                "type": "value_error",
            },
            {
                "loc": ["body", "categories"],
                "msg": "categories should be passed for AnnotationJob",
                "type": "value_error",
            },
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotation_job_excessive_data(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "validation_type": ValidationType.hierarchical,
            "owners": ["owner1", "owner2"],
            "annotators": ["annotator1", "annotator2"],
            "validators": ["validator1", "validator2"],
            "categories": ["category1", "category2"],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
            "pipeline_name": "pipeline",
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "pipeline_name"],
                "msg": "pipeline_name cannot be assigned to AnnotationJob",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_extraction_job_lack_of_data(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "test_extraction_job",
            "type": "ExtractionJob",
            "files": [1, 2],
            "datasets": [],
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "pipeline_name"],
                "msg": "pipeline cannot be empty for ExtractionJob",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_extraction_job_excessive_data(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "test_extraction_job",
            "type": "ExtractionJob",
            "files": [1, 2],
            "datasets": [],
            "pipeline_name": "pipeline",
            "categories": ["category1", "category2"],
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "categories"],
                "msg": "categories cannot be assigned to ExtractionJob",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_extraction_with_annotation_job_lack_of_data(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockExtractionWithAnnotationJob",
            "type": "ExtractionWithAnnotationJob",
            "datasets": [1, 2],
            "users": [1, 2],
            "files": [1, 2],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
            "is_draft": False,
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "pipeline_name"],
                "msg": "pipeline cannot be empty for "
                "ExtractionWithAnnotationJob",
                "type": "value_error",
            }
        ]
    }


# ------- Test validation_type, annotators, validators fields ------ #


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotation_job_cross_validation_with_validators(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "validation_type": ValidationType.cross,
            "owners": ["owner1"],
            "annotators": ["annotator1", "annotator2"],
            "validators": ["validator1"],
            "categories": ["category1", "category2"],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "validators"],
                "msg": "validators should be empty with "
                "validation_type=<ValidationType.cross: 'cross'>",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotation_job_cross_validation_without_annotators(
    testing_app,
):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "validation_type": ValidationType.cross,
            "owners": ["owner1"],
            "annotators": [],
            "validators": [],
            "categories": ["category1", "category2"],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "annotators"],
                "msg": "annotators cannot be empty with "
                "validation_type=<ValidationType.cross: 'cross'>",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotation_job_cross_validation_annotators_not_enough(
    testing_app,
):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "validation_type": ValidationType.cross,
            "owners": ["owner1"],
            "annotators": ["annotator1"],
            "validators": [],
            "categories": ["category1", "category2"],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "annotators"],
                "msg": "annotators should include at least 2 annotators with "
                "validation_type=<ValidationType.cross: 'cross'>",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotation_job_hierarchichal_validation_without_validators(
    testing_app,
):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "validation_type": ValidationType.hierarchical,
            "owners": ["owner1"],
            "annotators": ["annotator1", "annotator2"],
            "validators": [],
            "categories": ["category1", "category2"],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "validators"],
                "msg": "validators cannot be empty with "
                "validation_type=<ValidationType.hierarchical: "
                "'hierarchical'>",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_extraction_job_with_validators_field(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "test_extraction_job",
            "type": "ExtractionJob",
            "files": [1, 2],
            "datasets": [],
            "pipeline_name": "pipeline",
            "validators": ["validator1", "validator2"],
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "validators"],
                "msg": "validators cannot be assigned to ExtractionJob",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotationjob_validation_only_validation_type_with_annotators(
    testing_app,
):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "validation_type": ValidationType.validation_only,
            "owners": ["owner1"],
            "annotators": ["annotator1", "annotator2"],
            "validators": ["validator1"],
            "categories": ["category1", "category2"],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "annotators"],
                "msg": "annotators should be empty with "
                "validation_type=<ValidationType.validation_only: "
                "'validation only'>",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_create_annotationjob_validation_only_validation_type_no_validators(
    testing_app,
):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "MockAnnotationJob",
            "type": "AnnotationJob",
            "datasets": [1, 2],
            "files": [],
            "validation_type": ValidationType.validation_only,
            "owners": ["owner1"],
            "annotators": [],
            "validators": [],
            "categories": ["category1", "category2"],
            "is_auto_distribution": False,
            "deadline": str(
                datetime.datetime.utcnow() + datetime.timedelta(days=1)
            ),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "validators"],
                "msg": "validators cannot be empty with "
                "validation_type=<ValidationType.validation_only: "
                "'validation only'>",
                "type": "value_error",
            }
        ]
    }


# ------- Test ImportJob arguments validation ------ #


@pytest.mark.skip(reason="tests refactoring")
def test_empty_format_field(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "import_job_name",
            "type": "ImportJob",
            "import_source": "s3bucket_path",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "import_format"],
                "msg": "import_format cannot be empty in ImportJob",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_empty_s3bucket_field(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "import_job_name",
            "type": "ImportJob",
            "import_format": "jpg",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "import_source"],
                "msg": "import_source cannot be empty in ImportJob",
                "type": "value_error",
            }
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_for_excessive_format_and_s3bucket_not_in_ImportJob(testing_app):
    response = testing_app.post(
        "/jobs/create_job",
        json={
            "name": "test_extraction_job",
            "type": "ExtractionJob",
            "files": [1],
            "datasets": [2],
            "is_draft": False,
            "pipeline_name": "pipeline",
            "import_source": "some_value",
            "import_format": "some_value",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "import_source"],
                "msg": "import_source cannot be assigned to ExtractionJob",
                "type": "value_error",
            },
            {
                "loc": ["body", "import_format"],
                "msg": "import_format cannot be assigned to ExtractionJob",
                "type": "value_error",
            },
        ]
    }


@pytest.mark.skip(reason="tests refactoring")
def test_params_validation_for_extracting_job():
    request = {
        "name": "SuperExtraction",
        "files": [
            698
        ],
        "datasets": [],
        "type": "ExtractionJob",
        "is_draft": False,
        "is_auto_distribution": False,
        "start_manual_job_automatically": False,
        "owners": [
            "02336646-f5d0-4670-b111-c140a3ad58b5"
        ],
        "annotators": [],
        "validators": [],
        "pipeline_name": "dod latex",
        "pipeline_version": 1
    }
    assert JobParams.parse_obj(request)
