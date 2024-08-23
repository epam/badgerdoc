import uuid
from collections import namedtuple
from typing import Set, Tuple
from unittest.mock import MagicMock, call, patch
from uuid import UUID

import pytest

from annotation.errors import FieldConstraintError
from annotation.jobs import services
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobInfoSchema,
    JobStatusEnumSchema,
    JobTypeEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)


@pytest.fixture
def users():
    yield (
        User(user_id=UUID(int=0)),
        User(user_id=UUID(int=1)),
        User(user_id=UUID(int=2)),
        User(user_id=UUID(int=3)),
        User(user_id=UUID(int=4)),
    )


@pytest.fixture
def categories():
    yield Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    )


@pytest.fixture
def jobs_to_test_progress(users: Tuple[User], categories: Category):
    yield (
        Job(
            job_id=1,
            name="test1",
            callback_url="http://www.test.com",
            annotators=list(users[:2]),
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=[categories],
            deadline="2021-10-19T01:01:01",
            tenant="test",
            extensive_coverage=1,
        ),
        Job(
            job_id=2,
            name="test2",
            callback_url="http://www.test.com",
            annotators=list(users[:2]),
            validation_type=ValidationSchema.validation_only,
            is_auto_distribution=False,
            categories=[categories],
            deadline="2021-10-19T01:01:01",
            tenant="test",
            extensive_coverage=1,
        ),
    )


@pytest.fixture
def tasks():
    status = (
        TaskStatusEnumSchema.finished,
        TaskStatusEnumSchema.in_progress,
        TaskStatusEnumSchema.ready,
        TaskStatusEnumSchema.pending,
        TaskStatusEnumSchema.ready,
        TaskStatusEnumSchema.pending,
    )
    tasks = []
    for i in range(1, 7):
        tasks.append(
            ManualAnnotationTask(
                id=i,
                file_id=i if i != 6 else 1,
                pages=[1] if i != 5 else [3],
                job_id=i if i < 4 else 10,
                user_id="7b626e68-857d-430a-b65b-bba0a40417ee",
                is_validation=False if i < 5 else True,
                status=status[i - 1],
                deadline=None,
            )
        )
    yield tasks


@pytest.fixture
def files():
    yield (
        File(
            file_id=1,
            tenant="tenant",
            job_id=1,
            pages_number=100,
            status=FileStatusEnumSchema.pending,
        ),
        File(
            file_id=2,
            tenant="tenant",
            job_id=1,
            pages_number=150,
            status=FileStatusEnumSchema.pending,
        ),
    )


def test_update_inner_job_status():
    mock_session = MagicMock()
    services.update_inner_job_status(
        mock_session, 1, JobStatusEnumSchema.finished
    )
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
        services.check_annotators(annotators, validation_type)


def test_collect_job_names_all_db(jobs_to_test_progress: Tuple[Job, ...]):
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = [
        jobs_to_test_progress[0],
        jobs_to_test_progress[1],
    ]
    expected_result = {1: "test1", 2: "test2"}
    result = services.collect_job_names(mock_session, [1, 2], "test", "token")
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
        result = services.collect_job_names(
            mock_session, [1, 2], "test", "token"
        )
        mock_update_jobs_names.assert_called_once()
        assert result == expected_result


def test_get_jobs_by_name():
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = (
        (1, "test1"),
        (2, "test2"),
    )
    expected_result = {1: "test1", 2: "test2"}
    result = services.get_jobs_by_name(
        mock_session, ("test1", "test2"), "test"
    )
    assert result == expected_result


def test_update_jobs_names():
    mock_session = MagicMock()
    services.update_jobs_names(mock_session, {1: "test1", 2: "test2"})
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
    with pytest.raises(services.JobNotFoundError):
        services.update_jobs_categories(mock_session, "1", (categories,))


def test_update_jobs_categories(categories: Category):
    mock_session = MagicMock()
    mock_job = namedtuple("mock_job", ["job_id", "categories"])
    mock_categories = MagicMock()
    mock_categories.id = 1
    mock_session.query().filter().with_for_update().first.return_value = (
        mock_job(1, mock_categories)
    )
    services.update_jobs_categories(mock_session, "1", (categories,))
    mock_categories.extend.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_pages_in_work(tasks: Tuple[ManualAnnotationTask, ...]):
    expected_result = {
        "validation": [
            {"file_id": tasks[0].file_id, "pages_number": tasks[0].pages}
        ],
        "annotation": [
            {"file_id": tasks[5].file_id, "pages_number": tasks[5].pages}
        ],
    }
    result = services.get_pages_in_work(
        {tasks[0], tasks[1], tasks[5]}, {tasks[1]}
    )
    assert result == expected_result


def test_get_tasks_to_delete(tasks: Tuple[ManualAnnotationTask, ...]):
    expected_result = {tasks[4], tasks[3], tasks[2]}
    result = services.get_tasks_to_delete(
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
        result = services.get_jobs_by_files(
            mock_session, {1, 2, 3}, "test", "test"
        )
        assert result == expected_result


def test_get_job_attributes_for_post_attribute_job(
    jobs_to_test_progress: Tuple[Job, ...]
):
    job_id = 1
    mock_session = MagicMock()
    mock_session.query().filter_by().first.return_value = (
        jobs_to_test_progress[0]
    )
    expected_result = jobs_to_test_progress[0]
    result = services.get_job_attributes_for_post(
        mock_session, job_id, "test", (Job,)
    )
    assert result == expected_result


def test_get_job_attributes_for_post_attribute_columns():
    job_id = 1
    mock_session = MagicMock()
    mock_session.query().filter_by().first.return_value = (
        "job_name_2",
        JobStatusEnumSchema.finished,
    )
    expected_result = ("job_name_2", JobStatusEnumSchema.finished)
    result = services.get_job_attributes_for_post(
        mock_session, job_id, "test", (Job.name, Job.status)
    )
    assert result == expected_result


def test_get_job_attributes_for_post_attribute_not_found():
    job_id = 1
    mock_session = MagicMock()
    mock_session.query().filter_by().first.return_value = None
    with pytest.raises(FieldConstraintError):
        services.get_job_attributes_for_post(
            mock_session, job_id, "test", (Job.name,)
        )


def test_recalculate_file_pages(files: Tuple[File]):
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_session.query().filter.return_value = mock_result
    expected_validating_pages = [5, 7]
    expected_annotating_pages = [3, 5, 6, 7]

    filter_side_effect = (
        lambda *args: MagicMock(
            all=MagicMock(return_value=[([5, 6, 7],), ([3, 6],)])
        )
        if "NOT" in str(args[0])
        else MagicMock(all=MagicMock(return_value=[([5, 7],)]))
    )
    mock_result.filter.side_effect = filter_side_effect
    services.recalculate_file_pages(mock_session, files[0])
    assert files[0].distributed_validating_pages == expected_validating_pages
    assert files[0].distributed_annotating_pages == expected_annotating_pages


def test_read_user(users: Tuple[User]):
    mock_session = MagicMock()
    mock_session.query().get.return_value = users[0]
    result = services.read_user(mock_session, users[0])
    assert result == users[0]


def test_create_user():
    mock_session = MagicMock()
    expected_result = User(user_id=1)
    result = services.create_user(mock_session, 1)
    assert result == expected_result


# TODO .dict method converts JobInfoSchema values to
# sets and they need to be list
# TODO Job constructor needs references to User object instead of UUID
# for fields annotators, validators, owners
# TODO same thing for fields files, categories and tasks
@pytest.mark.skip(reason="can not create Job with JobSchema")
def test_create_job():
    mock_session = MagicMock()
    expected_result = Job(
        job_id=1,
        name="test1",
        callback_url="http://www.test.com",
        annotators=[None],
        files=[None],
        is_auto_distribution=False,
        categories=[None],
        deadline=None,
        job_type=JobTypeEnumSchema.ExtractionJob,
        tenant="test",
    )
    result = services.create_job(
        mock_session,
        JobInfoSchema(
            job_id=1,
            name="test1",
            callback_url="http://www.test.com",
            annotators=set(),
            files={1},
            validators=set(),
            owners={uuid.UUID("82533770-a99e-4873-8b23-6bbda86b59ae")},
            previous_jobs=[],
            datasets={1, 2},
            is_auto_distribution=False,
            categories=set(),
            deadline=None,
            job_type=JobTypeEnumSchema.ExtractionJob,
            tenant="test",
        ),
    )
    assert result == expected_result


def test_add_users(users: Tuple[User, ...]):
    mock_session = MagicMock()
    cur_users = [users[1], users[2]]
    new_user_ids = {UUID(int=3), UUID(int=4)}
    expected_result = [
        users[1],
        users[2],
        users[3],
    ]
    mock_session.query().filter().all.return_value = [users[3]]
    result = services.add_users(mock_session, cur_users, new_user_ids)
    assert result == expected_result


def test_update_job_categories(categories: Category):
    mock_session = MagicMock()
    patch_data = {"categories": [1, 2, 3]}
    expected_result = ["18d3d189e73a4680bfa77ba3fe6ebee5"]
    tenat = "test"
    with patch(
        "annotation.jobs.services.fetch_bunch_categories_db",
        return_value=[categories],
    ):
        services.update_job_categories(mock_session, patch_data, tenat)
        assert [cat.id for cat in patch_data["categories"]] == expected_result


@pytest.mark.parametrize(
    ("patch_data"),
    (
        {
            "extensive_coverage": 1,
            "annotators": [
                User(user_id=UUID(int=1)),
                User(user_id=UUID(int=2)),
            ],
        },
        {"extensive_coverage": 1, "annotators": []},
    ),
)
def test_validate_job_extensive_coverage_success(
    patch_data: dict, users: Tuple[User, ...]
):
    job = Job(annotators=list(users[3:4]))
    services.validate_job_extensive_coverage(patch_data, job)


@pytest.mark.parametrize(
    ("patch_data"),
    (
        {
            "extensive_coverage": 5,
            "annotators": [
                User(user_id=UUID(int=1)),
                User(user_id=UUID(int=2)),
            ],
        },
        {"extensive_coverage": 5, "annotators": []},
    ),
)
def test_validate_job_extensive_coverage_error(
    patch_data: dict, users: Tuple[User, ...]
):
    job = Job(annotators=list(users[3:4]))
    with pytest.raises(FieldConstraintError):
        services.validate_job_extensive_coverage(patch_data, job)


def test_update_job_files(files: Tuple[File]):
    mock_session = MagicMock()
    patch_data = {"files": {1, 2}, "datasets": {"dataset1"}}
    expected_calls = list(files[:2])

    with patch(
        "annotation.jobs.services.get_files_info",
        return_value=[
            {"file_id": 1, "pages_number": 100},
            {"file_id": 2, "pages_number": 150},
        ],
    ):
        services.update_job_files(
            mock_session, patch_data, 1, "tenant", "token"
        )
        mock_session.add_all.assert_called_once_with(expected_calls)
        mock_session.query().filter_by.assert_called_once_with(job_id=1)
        mock_session.query().filter_by().delete.assert_called_once()


def test_update_user_overall_load(tasks: Tuple[ManualAnnotationTask]):
    mock_session = MagicMock()
    mock_user = User(user_id=UUID(int=1))
    mock_session.query().filter().all.return_value = (
        tasks[0],
        tasks[1],
        tasks[2],
        tasks[3],
    )
    mock_session.query().get.return_value = mock_user
    services.update_user_overall_load(mock_session, UUID(int=1))
    assert mock_user.overall_load == 3
    mock_session.add.assert_called_once_with(mock_user)
