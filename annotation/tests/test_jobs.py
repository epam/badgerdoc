import unittest
import uuid
from collections import namedtuple
from typing import Set, Tuple, Union
from unittest.mock import MagicMock, call, patch
from uuid import UUID

import pytest

import annotation.jobs.services
from annotation.errors import FieldConstraintError
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
            annotators=[users[0], users[1]],
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
            annotators=[users[0], users[1]],
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
                user_id=UUID(int=i),
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
            distributed_validating_pages=[],
            distributed_annotating_pages=[],
        ),
        File(
            file_id=2,
            tenant="tenant",
            job_id=1,
            pages_number=150,
            status=FileStatusEnumSchema.pending,
            distributed_validating_pages=[],
            distributed_annotating_pages=[],
        ),
    )


def test_update_inner_job_status():
    mock_session = MagicMock()
    annotation.jobs.services.update_inner_job_status(
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
        annotation.jobs.services.check_annotators(annotators, validation_type)


def test_collect_job_names_all_db(jobs_to_test_progress: Tuple[Job, ...]):
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = [
        jobs_to_test_progress[0],
        jobs_to_test_progress[1],
    ]
    expected_result = {1: "test1", 2: "test2"}
    result = annotation.jobs.services.collect_job_names(
        mock_session, [1, 2], "test", "token"
    )
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
        result = annotation.jobs.services.collect_job_names(
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
    result = annotation.jobs.services.get_jobs_by_name(
        mock_session, ("test1", "test2"), "test"
    )
    assert result == expected_result


def test_update_jobs_names():
    mock_session = MagicMock()
    annotation.jobs.services.update_jobs_names(
        mock_session, {1: "test1", 2: "test2"}
    )
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
    with pytest.raises(annotation.jobs.services.JobNotFoundError):
        annotation.jobs.services.update_jobs_categories(
            mock_session, "1", (categories,)
        )


def test_update_jobs_categories(categories: Category):
    mock_session = MagicMock()
    mock_job = namedtuple("mock_job", ["job_id", "categories"])
    mock_categories = MagicMock()
    mock_categories.id = 1
    mock_session.query().filter().with_for_update().first.return_value = (
        mock_job(1, mock_categories)
    )
    annotation.jobs.services.update_jobs_categories(
        mock_session, "1", (categories,)
    )
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
    result = annotation.jobs.services.get_pages_in_work(
        {tasks[0], tasks[1], tasks[5]}, {tasks[1]}
    )
    assert result == expected_result


def test_get_tasks_to_delete(tasks: Tuple[ManualAnnotationTask, ...]):
    expected_result = {tasks[4], tasks[3], tasks[2]}
    result = annotation.jobs.services.get_tasks_to_delete(
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
        result = annotation.jobs.services.get_jobs_by_files(
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
    result = annotation.jobs.services.get_job_attributes_for_post(
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
    result = annotation.jobs.services.get_job_attributes_for_post(
        mock_session, job_id, "test", (Job.name, Job.status)
    )
    assert result == expected_result


def test_get_job_attributes_for_post_attribute_not_found():
    job_id = 1
    mock_session = MagicMock()
    mock_session.query().filter_by().first.return_value = None
    with pytest.raises(FieldConstraintError):
        annotation.jobs.services.get_job_attributes_for_post(
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
    annotation.jobs.services.recalculate_file_pages(mock_session, files[0])
    assert files[0].distributed_validating_pages == expected_validating_pages
    assert files[0].distributed_annotating_pages == expected_annotating_pages


def test_read_user(users: Tuple[User]):
    mock_session = MagicMock()
    mock_session.query().get.return_value = users[0]
    result = annotation.jobs.services.read_user(mock_session, users[0])
    assert result == users[0]


def test_create_user():
    mock_session = MagicMock()
    expected_result = User(user_id=1)
    result = annotation.jobs.services.create_user(mock_session, 1)
    assert result == expected_result


# can not create Job with JobSchema
@pytest.mark.skip(reason="Does not work")
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
    result = annotation.jobs.services.create_job(
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
    result = annotation.jobs.services.add_users(
        mock_session, cur_users, new_user_ids
    )
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
        annotation.jobs.services.update_job_categories(
            mock_session, patch_data, tenat
        )
        assert [cat.id for cat in patch_data["categories"]] == expected_result


@pytest.mark.parametrize(
    ("patch_data", "user_id"),
    (
        (
            {
                "extensive_coverage": 1,
                "annotators": [
                    User(user_id=UUID(int=1)),
                    User(user_id=UUID(int=2)),
                ],
            },
            (
                3,
                4,
            ),
        ),
        (
            {"extensive_coverage": 1, "annotators": []},
            (
                3,
                4,
            ),
        ),
        (
            {
                "extensive_coverage": 5,
                "annotators": [
                    User(user_id=UUID(int=1)),
                    User(user_id=UUID(int=2)),
                ],
            },
            (
                3,
                4,
            ),
        ),
        (
            {"extensive_coverage": 5, "annotators": []},
            (
                3,
                4,
            ),
        ),
    ),
)
def test_validate_job_extensive_coverage(
    patch_data: dict, user_id: Tuple[int], users: Tuple[User, ...]
):
    job = Job(annotators=[users[i] for i in user_id])
    if patch_data.get("extensive_coverage") == 5:
        with pytest.raises(FieldConstraintError):
            annotation.jobs.services.validate_job_extensive_coverage(
                patch_data, job
            )


def test_update_job_files(files: Tuple[File]):
    mock_session = MagicMock()
    patch_data = {"files": {1, 2}, "datasets": {"dataset1"}}
    for i in range(2):
        files[i].distributed_annotating_pages = None
        files[i].distributed_validating_pages = None
    expected_calls = [files[0], files[1]]

    with patch(
        "annotation.jobs.services.get_files_info",
        return_value=[
            {"file_id": 1, "pages_number": 100},
            {"file_id": 2, "pages_number": 150},
        ],
    ):
        annotation.jobs.services.update_job_files(
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
    annotation.jobs.services.update_user_overall_load(
        mock_session, UUID(int=1)
    )
    assert mock_user.overall_load == 3
    mock_session.add.assert_called_once_with(mock_user)


def test_find_users():
    mock_session = MagicMock()
    expected_saved_users = [User(user_id=UUID(int=1))]
    expected_new_users = [User(user_id=UUID(int=2))]
    mock_session.query().filter().all.return_value = [
        User(user_id=UUID(int=1))
    ]
    result_saved_users, result_new_users = annotation.jobs.services.find_users(
        mock_session, set((UUID(int=1), UUID(int=2)))
    )
    assert result_saved_users == expected_saved_users
    assert result_new_users == expected_new_users


@pytest.mark.parametrize(
    ("mock_query",), ((Job(job_id=1, tenant="tenant"),), (None,))
)
def test_get_job(mock_query: Union[Job, None]):
    mock_session = MagicMock()
    mock_session.query().filter_by().first.return_value = mock_query
    if not mock_query:
        with pytest.raises(annotation.jobs.services.WrongJobError):
            annotation.jobs.services.get_job(mock_session, 1, "tenant")
    else:
        result = annotation.jobs.services.get_job(mock_session, 1, "tenant")
        expected_result = Job(job_id=1, tenant="tenant")
        assert result == expected_result


# why are tasks in this function dict
def test_update_files(files: Tuple[File]):
    mock_session = MagicMock()
    mock_session.query().filter().with_for_update().all.return_value = [
        files[0],
        files[1],
    ]
    tasks = [
        {"file_id": 1, "is_validation": True, "pages": [1, 2, 3]},
        {"file_id": 2, "is_validation": False, "pages": [4, 5, 6]},
    ]
    annotation.jobs.services.update_files(mock_session, tasks, 1)
    assert files[0].distributed_validating_pages == [1, 2, 3]
    assert files[1].distributed_annotating_pages == [4, 5, 6]


def test_delete_tasks(tasks: Tuple[ManualAnnotationTask], files: Tuple[File]):
    mock_session = MagicMock()
    mock_session.query().filter().with_for_update().first.return_value = files[
        0
    ]
    expected_delete_calls = [
        unittest.mock.call(tasks[0]),
        unittest.mock.call(tasks[5]),
    ]

    expected_recalculate_calls = files[0]
    expected_user_load_calls = [
        unittest.mock.call(mock_session, tasks[0].user_id),
        unittest.mock.call(mock_session, tasks[5].user_id),
    ]
    with patch(
        "annotation.jobs.services.recalculate_file_pages"
    ) as mock_recalculate_file_pages, patch(
        "annotation.jobs.services.update_user_overall_load"
    ) as mock_update_user_overall_load:
        annotation.jobs.services.delete_tasks(
            mock_session, {tasks[0], tasks[5]}
        )
        mock_session.delete.assert_has_calls(
            expected_delete_calls, any_order=True
        )
        mock_recalculate_file_pages.assert_called_with(
            mock_session, expected_recalculate_calls
        )
        mock_update_user_overall_load.assert_has_calls(
            expected_user_load_calls, any_order=True
        )


@pytest.mark.parametrize(
    (
        "new_validators",
        "new_annotators",
        "job_validators",
        "job_annotators",
        "expected_annotators",
        "expected_validators",
    ),
    (
        (
            {UUID(int=1), UUID(int=2)},
            {UUID(int=3)},
            (User(user_id=UUID(int=1)), User(user_id=UUID(int=2))),
            (User(user_id=UUID(int=3)), User(user_id=UUID(int=4))),
            {UUID(int=4)},
            set(),
        ),
        (
            {UUID(int=3)},
            {UUID(int=2), UUID(int=1)},
            (User(user_id=UUID(int=4)), User(user_id=UUID(int=3))),
            (User(user_id=UUID(int=2)), User(user_id=UUID(int=1))),
            set(),
            {UUID(int=4)},
        ),
    ),
)
def test_find_saved_users(
    new_validators: Set[UUID],
    new_annotators: Set[UUID],
    job_validators: Tuple[User],
    job_annotators: Tuple[User],
    expected_annotators: Set[UUID],
    expected_validators: Set[UUID],
):
    mock_session = MagicMock()

    mock_job = MagicMock()
    mock_job.validators = job_validators
    mock_job.annotators = job_annotators
    with patch(
        "annotation.jobs.services.delete_tasks_for_removed_users",
        return_value=[ManualAnnotationTask(user_id=UUID(int=4))],
    ):
        (
            result_annotators,
            result_validators,
        ) = annotation.jobs.services.find_saved_users(
            mock_session, mock_job, new_annotators, new_validators
        )
        assert result_validators == expected_validators
        assert result_annotators == expected_annotators


@pytest.mark.parametrize(
    (
        "patch_data",
        "is_manual",
        "expected_deleted",
        "expected_annotators",
        "expected_validators",
    ),
    (
        (
            {
                "annotators": {UUID(int=5)},
                "validators": {UUID(int=6)},
                "owners": {UUID(int=7)},
            },
            True,
            {UUID(int=1), UUID(int=2), UUID(int=3), UUID(int=4)},
            set(),
            set(),
        ),
        (
            {
                "annotators": {UUID(int=1)},
                "validators": {UUID(int=2)},
                "owners": {UUID(int=4)},
            },
            True,
            {UUID(int=3)},
            set(),
            set(),
        ),
        (
            {
                "annotators": {UUID(int=1)},
                "validators": {UUID(int=2)},
                "owners": {UUID(int=4)},
            },
            False,
            set(),
            set(),
            set(),
        ),
    ),
)
def test_update_jobs_users(
    patch_data,
    is_manual,
    expected_deleted,
    expected_annotators,
    expected_validators,
):
    mock_session = MagicMock()
    mock_job = MagicMock()
    mock_job.annotators = [
        User(user_id=UUID(int=1)),
        User(user_id=UUID(int=2)),
    ]
    mock_job.validators = [
        User(user_id=UUID(int=2)),
        User(user_id=UUID(int=3)),
    ]
    mock_job.owners = [User(user_id=UUID(int=4))]

    # Need to also mock the dependent functions
    with patch(
        "annotation.jobs.services.find_saved_users",
        return_value=(set(), set()),
    ), patch(
        "annotation.jobs.services.find_users", return_value=([], [])
    ), patch(
        "annotation.jobs.services.check_annotators"
    ) as mock_check_annotators, patch(
        "annotation.jobs.services.check_validators"
    ) as mock_check_validators:
        (
            deleted_users,
            annotators_to_save,
            validators_to_save,
        ) = annotation.jobs.services.update_jobs_users(
            mock_session, mock_job, patch_data, is_manual
        )
        assert deleted_users == expected_deleted
        assert annotators_to_save == expected_annotators
        assert validators_to_save == expected_validators
        if is_manual:
            mock_check_annotators.assert_called_once()
            mock_check_validators.assert_called_once()


def test_delete_redudant_users():
    mock_session = MagicMock()
    mock_users = MagicMock()
    mock_session.query().join.return_value = mock_users
    deleted_uuid = UUID(int=1)
    active_uuid = UUID(int=2)
    mock_users.union().union().all.return_value = [User(user_id=active_uuid)]
    with patch("annotation.jobs.services.User.user_id.in_") as mock_in:
        annotation.jobs.services.delete_redundant_users(
            mock_session, {deleted_uuid, active_uuid}
        )
        mock_in.assert_called_once_with({deleted_uuid})


def test_set_task_statuses_annotation_task_finished(
    tasks: Tuple[ManualAnnotationTask, ...],
    jobs_to_test_progress: Tuple[Job, ...],
):
    annotation.jobs.services.set_task_statuses(
        jobs_to_test_progress[0], (tasks[0], tasks[5])
    )
    assert tasks[5].status == TaskStatusEnumSchema.ready
    assert tasks[0].status == TaskStatusEnumSchema.finished


def test_set_task_statuses_job_validaiton_only(
    tasks: Tuple[ManualAnnotationTask, ...],
    jobs_to_test_progress: Tuple[Job, ...],
):
    annotation.jobs.services.set_task_statuses(
        jobs_to_test_progress[1], (tasks[1], tasks[5])
    )
    assert tasks[5].status == TaskStatusEnumSchema.ready


def test_set_task_statuses_pages_not_annotated(
    tasks: Tuple[ManualAnnotationTask, ...],
    jobs_to_test_progress: Tuple[Job, ...],
):
    tasks[5].pages = [1, 2]
    annotation.jobs.services.set_task_statuses(
        jobs_to_test_progress[0], (tasks[0], tasks[5])
    )
    assert tasks[5].status == TaskStatusEnumSchema.pending


@pytest.mark.parametrize(
    "tasks, pages_in_work, expected_tasks",
    [
        (
            [
                {"file_id": 1, "pages": [1, 2, 3, 4, 5], "is_urgent": True},
                {"file_id": 2, "pages": [6, 7, 8, 9, 10], "is_urgent": False},
                {"file_id": 1, "pages": [11, 12, 13], "is_urgent": True},
            ],
            [
                {"file_id": 1, "pages_number": [1, 2, 3]},
                {"file_id": 2, "pages_number": [7, 8]},
            ],
            [
                {"file_id": 1, "pages": [4, 5], "is_urgent": True},
                {"file_id": 2, "pages": [6, 9, 10], "is_urgent": False},
                {"file_id": 1, "pages": [11, 12, 13], "is_urgent": True},
            ],
        ),
        (
            [{"file_id": 3, "pages": [14, 15], "is_urgent": True}],
            [{"file_id": 1, "pages_number": [1, 2, 3]}],
            [{"file_id": 3, "pages": [14, 15], "is_urgent": True}],
        ),
        (
            [{"file_id": 1, "pages": [1, 2, 3], "is_urgent": True}],
            [{"file_id": 1, "pages_number": [1, 2, 3]}],
            [],
        ),
    ],
)
def test_remove_pages_in_work(tasks, pages_in_work, expected_tasks):
    annotation.jobs.services.remove_pages_in_work(tasks, pages_in_work)
    assert tasks == expected_tasks


def test_delete_tasks_for_removed_users(
    tasks: Tuple[ManualAnnotationTask, ...], users: Tuple[User, ...]
):
    mock_session = MagicMock()
    mock_session.query().filter().all.return_value = [tasks[0], tasks[1]]
    with patch("annotation.jobs.services.delete_tasks") as mock_delete_tasks:
        result = annotation.jobs.services.delete_tasks_for_removed_users(
            mock_session, {users[0].user_id, users[1].user_id}, 1, False
        )
        expected_result = {tasks[0]}
        assert result == expected_result
        mock_delete_tasks.assert_called_once_with(mock_session, {tasks[1]})
