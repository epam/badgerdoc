import uuid
from collections import namedtuple
from typing import Any, Set, Tuple, Union
from unittest.mock import MagicMock, call, patch
from uuid import UUID

import pytest
from sqlalchemy.orm.attributes import InstrumentedAttribute

from annotation.database import Base
from annotation.errors import FieldConstraintError
from annotation.jobs.services import (
    JobNotFoundError,
    check_annotators,
    collect_job_names,
    get_job_attributes_for_post,
    get_jobs_by_files,
    get_jobs_by_name,
    get_pages_in_work,
    get_tasks_to_delete,
    update_inner_job_status,
    update_jobs_categories,
    update_jobs_names,
)
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)


@pytest.fixture
def job_annotators():
    yield (
        User(user_id="82533770-a99e-4873-8b23-6bbda86b59ae"),
        User(user_id="ef81a4d0-cc01-447b-9025-a70ed441672d"),
    )


@pytest.fixture
def categories():
    yield Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    )


@pytest.fixture
def jobs_to_test_progress(job_annotators: Tuple[User], categories: Category):
    yield (
        Job(
            job_id=1,
            name="test1",
            callback_url="http://www.test.com",
            annotators=[job_annotators[0], job_annotators[1]],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=[categories],
            deadline="2021-10-19T01:01:01",
            tenant="test",
        ),
        Job(
            job_id=2,
            name="test2",
            callback_url="http://www.test.com",
            annotators=[job_annotators[0], job_annotators[1]],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=[categories],
            deadline="2021-10-19T01:01:01",
            tenant="test",
        ),
    )


@pytest.fixture
def tasks():
    yield (
        ManualAnnotationTask(
            id=1,
            file_id=1,
            pages=[1],
            job_id=1,
            user_id="7b626e68-857d-430a-b65b-bba0a40417ee",
            is_validation=False,
            status=TaskStatusEnumSchema.in_progress,
            deadline=None,
        ),
        ManualAnnotationTask(
            id=2,
            file_id=2,
            pages=[1],
            job_id=2,
            user_id="7b626e68-857d-430a-b65b-bba0a40417ee",
            is_validation=False,
            status=TaskStatusEnumSchema.finished,
            deadline=None,
        ),
        ManualAnnotationTask(
            id=3,
            file_id=3,
            pages=[1],
            job_id=2,
            user_id="7b626e68-857d-430a-b65b-bba0a40417ea",
            is_validation=False,
            status=TaskStatusEnumSchema.ready,
            deadline=None,
        ),
        ManualAnnotationTask(
            id=4,
            file_id=4,
            pages=[1],
            job_id=10,
            user_id="7b626e68-857d-430a-b65b-bba0a40417eb",
            is_validation=False,
            status=TaskStatusEnumSchema.pending,
            deadline=None,
        ),
        ManualAnnotationTask(
            id=5,
            file_id=5,
            pages=[3],
            job_id=10,
            user_id="7b626e68-857d-430a-b65b-bba0a40417eb",
            is_validation=True,
            status=TaskStatusEnumSchema.ready,
            deadline=None,
        ),
        ManualAnnotationTask(
            id=6,
            file_id=1,
            pages=[1],
            job_id=10,
            user_id="7b626e68-857d-430a-b65b-bba0a40417eb",
            is_validation=True,
            status=TaskStatusEnumSchema.pending,
            deadline=None,
        ),
    )
    yield (
        Job(
            job_id=1,
            name="test1",
            callback_url="http://www.test.com",
            annotators=[job_annotators[0], job_annotators[1]],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=[categories],
            deadline="2021-10-19T01:01:01",
            tenant="test",
        ),
        Job(
            job_id=2,
            name="test2",
            callback_url="http://www.test.com",
            annotators=[job_annotators[0], job_annotators[1]],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=[categories],
            deadline="2021-10-19T01:01:01",
            tenant="test",
        ),
    )


@pytest.fixture
def files(jobs_to_test_progress: Job):
    yield File(
        file_id=1,
        tenant="test",
        job_id=jobs_to_test_progress[0].job_id,
        pages_number=5,
        status=FileStatusEnumSchema.pending,
    )


def test_update_inner_job_status():
    mock_session = MagicMock()
    update_inner_job_status(mock_session, 1, JobStatusEnumSchema.finished)
    mock_session.query(Job).filter(Job.job_id == 1).update.assert_called_with(
        {"status": JobStatusEnumSchema.finished}
    )


@pytest.mark.parametrize(
    (
        "validation_type",
        "annotators",
    ),
    (
        (
            ValidationSchema.cross,
            {uuid.UUID("82533770-a99e-4873-8b23-6bbda86b59ae")},
        ),
        (ValidationSchema.hierarchical, set()),
        (
            ValidationSchema.validation_only,
            {uuid.UUID("82533770-a99e-4873-8b23-6bbda86b59ae")},
        ),
    ),
)
def test_check_annotators(
    validation_type: ValidationSchema, annotators: Set[UUID]
):
    with pytest.raises(FieldConstraintError):
        check_annotators(annotators, validation_type)


def test_collect_job_names_all_db(jobs_to_test_progress: Tuple[Job]):
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = [
        jobs_to_test_progress[0],
        jobs_to_test_progress[1],
    ]
    expected_result = {1: "test1", 2: "test2"}
    result = collect_job_names(mock_session, [1, 2], "test", "token")
    assert result == expected_result


def test_collect_job_names_not_all_db():
    mock_session = MagicMock()
    mock_job = namedtuple("mock_job", ["job_id", "name"])
    mock_session.query().filter().all.return_value = [
        mock_job(1, "test1"),
        mock_job(2, None),
    ]
    expected_result = {1: "test1", 2: "test2"}
    with patch(
        "annotation.jobs.services.get_job_names",
        return_value=[mock_job(2, "test2")],
    ), patch(
        "annotation.jobs.services.update_jobs_names"
    ) as mock_update_jobs_names:
        result = collect_job_names(mock_session, [1, 2], "test", "token")
        mock_update_jobs_names.assert_called_once()
        assert result == expected_result


def test_get_jobs_by_name():
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = (
        (1, "test1"),
        (2, "test2"),
    )
    expected_result = {1: "test1", 2: "test2"}
    result = get_jobs_by_name(mock_session, ("test1", "test2"), "test")
    assert result == expected_result


def test_update_jobs_names():
    mock_session = MagicMock()
    update_jobs_names(mock_session, {1: "test1", 2: "test2"})
    expected_calls = [
        call({Job.name: "test1"}),
        call({Job.name: "test2"}),
    ]
    mock_session.query().filter(Job.job_id == 1).update.assert_has_calls(
        expected_calls, any_order=True
    )
    mock_session.commit.assert_called_once()


def test_update_jobs_categories_no_job(categories: Category):
    mock_session = MagicMock()
    mock_session.query().filter().with_for_update().first.return_value = None
    with pytest.raises(JobNotFoundError):
        update_jobs_categories(mock_session, "1", (categories,))


def test_update_jobs_categories(categories: Category):
    mock_session = MagicMock()
    mock_job = namedtuple("mock_job", ["job_id", "categories"])
    mock_categories = MagicMock()
    mock_categories.id = 1
    mock_session.query().filter().with_for_update().first.return_value = (
        mock_job(1, mock_categories)
    )
    update_jobs_categories(mock_session, "1", (categories,))
    mock_categories.extend.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_pages_in_work(tasks: Tuple[ManualAnnotationTask]):
    expected_result = {
        "validation": [
            {"file_id": tasks[0].file_id, "pages_number": tasks[0].pages}
        ],
        "annotation": [
            {"file_id": tasks[5].file_id, "pages_number": tasks[5].pages}
        ],
    }
    result = get_pages_in_work({tasks[0], tasks[1], tasks[5]}, {tasks[1]})
    assert result == expected_result


def test_get_tasks_to_delete(tasks: Tuple[ManualAnnotationTask]):
    expected_result = {tasks[3], tasks[2]}
    result = get_tasks_to_delete(
        [tasks[0], tasks[1], tasks[2], tasks[3], tasks[4], tasks[5]]
    )
    assert result == expected_result


def test_get_jobs_by_files():
    mock_session = MagicMock()
    mock_session.query().join().order_by().all.return_value = (
        (1, 1, JobStatusEnumSchema.finished),
        (1, 2, JobStatusEnumSchema.pending),
        (2, 3, JobStatusEnumSchema.in_progress),
    )
    expected_result = {
        1: [
            {
                "id": 1,
                "name": "job_name_1",
                "status": JobStatusEnumSchema.finished,
            },
            {
                "id": 2,
                "name": "job_name_2",
                "status": JobStatusEnumSchema.pending,
            },
        ],
        2: [
            {"id": 3, "name": None, "status": JobStatusEnumSchema.in_progress}
        ],
    }
    with patch(
        "annotation.jobs.services.collect_job_names",
        return_value={1: "job_name_1", 2: "job_name_2"},
    ):
        result = get_jobs_by_files(mock_session, {1, 2, 3}, "test", "test")
        assert result == expected_result


@pytest.mark.parametrize(
    ("job_id", "attributes", "expected_result"),
    (
        (
            1,
            (Job,),
            Job(
                job_id=1,
                name="test1",
                callback_url="http://www.test.com",
                annotators=[User(user_id="1")],
                validation_type=ValidationSchema.cross,
                is_auto_distribution=False,
                categories=[categories],
                deadline="2021-10-19T01:01:01",
                tenant="test",
            ),
        ),
        (
            2,
            (Job.name, Job.status),
            ("job_name_2", JobStatusEnumSchema.finished),
        ),
        (3, (Job.name,), None),
    ),
)
def test_get_job_attributes_for_post(
    job_id: int,
    attributes: Union[Tuple[Base], Tuple[InstrumentedAttribute, ...]],
    expected_result: Union[Job, Tuple[Any]],
):
    mock_session = MagicMock()
    if job_id == 1:
        mock_session.query().filter_by().first.return_value = Job(
            job_id=1,
            name="test1",
            callback_url="http://www.test.com",
            annotators=[User(user_id="1")],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=[categories],
            deadline="2021-10-19T01:01:01",
            tenant="test",
        )
        result = get_job_attributes_for_post(
            mock_session, job_id, "test", attributes
        )
        assert result == expected_result
    elif job_id == 2:
        mock_session.query().filter_by().first.return_value = (
            "job_name_2",
            JobStatusEnumSchema.finished,
        )
        result = get_job_attributes_for_post(
            mock_session, job_id, "test", attributes
        )
        assert result == expected_result
    elif job_id == 3:
        mock_session.query().filter_by().first.return_value = None
        with pytest.raises(FieldConstraintError):
            get_job_attributes_for_post(
                mock_session, job_id, "test", attributes
            )
