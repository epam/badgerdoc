import contextlib
import json
import os
import random
from typing import Iterable, List
from unittest.mock import Mock, patch

import boto3
import pytest
import sqlalchemy
import sqlalchemy_utils
from moto import mock_s3
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import FlushError

import tests.test_get_accumulated_revisions as accumulated_revs
import tests.test_get_jobs_info_by_files as jobs_info_by_files
import tests.test_validation as validation
from alembic import command
from alembic.config import Config
from annotation.annotations import MANIFEST, S3_START_PATH
from annotation.categories import cache
from annotation.database import SQLALCHEMY_DATABASE_URL, Base
from annotation.jobs import update_user_overall_load
from annotation.models import (
    AnnotatedDoc,
    Category,
    DocumentLinks,
    File,
    Job,
    ManualAnnotationTask,
    User,
)
from annotation.schemas import (
    AnnotationStatisticsInputSchema,
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from annotation.tasks import add_task_stats_record
from annotation.utils import get_test_db_url
from tests.override_app_dependency import TEST_TENANT
from tests.test_annotators_overall_load import (
    OVERALL_LOAD_CREATED_TASKS,
    OVERALL_LOAD_JOBS,
    OVERALL_LOAD_USERS,
    TASK_FILES_OVERALL_LOAD,
    VALIDATED_DOC_OVERALL_LOAD,
)
from tests.test_delete_batch_tasks import (
    DELETE_BATCH_TASKS_ANNOTATOR,
    DELETE_BATCH_TASKS_FILE,
    DELETE_BATCH_TASKS_JOB,
    DIFF_STATUSES_TASKS,
)
from tests.test_finish_task import (
    CATEGORIES,
    CATEGORIES_2,
    FINISH_DOCS,
    FINISH_DOCS_CHECK_DELETED_ANNOTATOR,
    FINISH_TASK_1,
    FINISH_TASK_1_SAME_JOB,
    FINISH_TASK_2,
    FINISH_TASK_2_SAME_JOB,
    FINISH_TASK_CHECK_DELETE_USER_ANNOTATOR_1,
    FINISH_TASK_CHECK_DELETE_USER_ANNOTATOR_2,
    FINISH_TASK_CHECK_DELETE_USER_VALIDATOR,
    FINISH_TASK_FILE_1,
    FINISH_TASK_FILE_2,
    FINISH_TASK_FILE_3,
    FINISH_TASK_FILE_4,
    FINISH_TASK_JOB_1,
    FINISH_TASK_JOB_2,
    FINISH_TASK_JOB_3,
    FINISH_TASK_JOB_4,
    FINISH_TASK_USER_1,
    FINISH_TASK_USER_2,
    FINISH_TASK_USER_3,
    TASK_NOT_IN_PROGRESS_STATUS,
    TRANSFER_ANNOTATIONS_DOCS,
    TRANSFER_ANNOTATIONS_FILE,
    TRANSFER_ANNOTATIONS_JOB,
    TRANSFER_ANNOTATIONS_PAGES,
    TRANSFER_ANNOTATIONS_TASKS,
    VALIDATION_TASKS_TO_READY,
)
from tests.test_get_annotation_for_particular_revision import (
    PART_REV_ANNOTATOR,
    PART_REV_DOC,
    PART_REV_PAGES,
)
from tests.test_get_child_categories import (
    COMMON_CHILD_CATEGORIES,
    CYCLIC_TENANT_CHILD_CATEGORIES,
    OTHER_TENANT_CHILD_CATEGORY,
)
from tests.test_get_job import (
    GET_FILES,
    GET_JOBS,
    JOB_TEST_ANNOTATORS,
    JOB_TEST_REVISIONS,
)
from tests.test_get_job_files import GET_JOB_FILES, GET_JOB_FILES_JOBS
from tests.test_get_job_progress import (
    FILE_TEST_PROGRESS,
    JOBS_TO_TEST_PROGRESS,
    TASKS_TEST_PROGRESS,
)
from tests.test_get_pages_info import PAGES_INFO_ENTITIES
from tests.test_get_revisions import JOBS_IDS, PAGE, PAGES_PATHS, REVISIONS, USERS_IDS
from tests.test_get_revisions_without_annotation import (
    REV_WITHOUT_ANNOTATION_DOC_1,
    REV_WITHOUT_ANNOTATION_DOC_2,
    REV_WITHOUT_ANNOTATION_DOC_3,
    REV_WITHOUT_ANNOTATION_JOB,
    REV_WITHOUT_ANNOTATION_TASK,
)
from tests.test_get_unassigned_files import UNASSIGNED_FILES_ENTITIES
from tests.test_get_users_for_job import USERS_FOR_JOB_ANNOTATORS, USERS_FOR_JOB_JOBS
from tests.test_job_categories import CATEGORIES_USERS, MOCK_ID
from tests.test_post import POST_JOBS, TEST_POST_USERS
from tests.test_post_annotation import (
    ANNOTATION_VALIDATION_TASKS_PG,
    MANIFEST_IN_MINIO,
    POST_ANNOTATION_ANNOTATOR,
    POST_ANNOTATION_FILE_1,
    POST_ANNOTATION_JOB_1,
    POST_ANNOTATION_PG_DOC,
    POST_ANNOTATION_PG_TASK_1,
    POST_ANNOTATION_PG_TASK_2,
    POST_ANNOTATION_VALIDATION_JOB,
    POST_ANNOTATION_VALIDATOR,
    S3_PATH,
)
from tests.test_post_job import POST_JOB_EXISTING_JOB
from tests.test_post_next_task import NEXT_TASK_ANNOTATION_TASKS, NEXT_TASK_JOB
from tests.test_post_unassgined_files import (
    ANNOTATORS_POST_UN_FILES,
    JOBS_FILES_TASKS_POST_UN_FILES,
)
from tests.test_search_kafka import (
    ANNOTATION_KAFKA_FILE,
    ANNOTATION_KAFKA_JOB,
    ANNOTATION_KAFKA_TASK,
)
from tests.test_start_job import CHANGE_STATUSES_JOBS, CHANGE_STATUSES_TASKS
from tests.test_tasks_crud_cr import CRUD_CR_ANNOTATION_TASKS, CRUD_CR_JOBS
from tests.test_tasks_crud_cr import FILES as CRUD_CR_FILES
from tests.test_tasks_crud_ud import (
    CRUD_UD_CONSTRAINTS_FILES,
    CRUD_UD_CONSTRAINTS_JOBS,
    CRUD_UD_CONSTRAINTS_TASKS,
    CRUD_UD_CONSTRAINTS_USERS,
    CRUD_UD_JOB_1,
    CRUD_UD_JOB_2,
    CRUD_UD_TASK,
)
from tests.test_update_job import (
    NEW_REDISTRIBUTE_TASKS_CATEGORY,
    NEW_REDISTRIBUTE_TASKS_USER,
    REDISTRIBUTE_TASKS_FILE,
    REDISTRIBUTE_TASKS_JOB,
    REDISTRIBUTED_TASKS,
    UPDATE_JOB_CATEGORIES,
    UPDATE_JOB_FILES,
    UPDATE_JOB_USERS,
    UPDATE_JOBS,
    UPDATE_USER_NO_JOBS,
)

DEFAULT_REGION = "us-east-1"

alembic_cfg = Config("alembic.ini")

test_db_url = get_test_db_url(SQLALCHEMY_DATABASE_URL)
engine = create_engine(test_db_url)


@pytest.fixture(scope="module")
def setup_test_db(use_temp_env_var):
    if not sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.create_database(engine.url)
    else:
        # Drop all tables except 'alembic'
        Base.metadata.drop_all(bind=engine)

        # Drop 'alembic_revision_annotation' table
        with contextlib.closing(engine.connect()) as con:
            trans = con.begin()
            con.execute("DROP TABLE IF EXISTS alembic_revision_annotation ")
            trans.commit()

    # Ensure LTREE extensions is installed
    with engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.sql.text("CREATE EXTENSION LTREE"))
        except sqlalchemy.exc.ProgrammingError as err_:
            # Extension installed, just skip error
            if "DuplicateObject" not in str(err_):
                raise err_
    try:
        command.upgrade(alembic_cfg, "head")
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Got an Exception during migrations - {e}")


def close_session(gen):
    try:
        next(gen)
    except StopIteration:
        pass


def clear_db():
    """
    Clear db
    reversed(Base.metadata.sorted_tables) makes
    it so children are deleted before parents.
    """
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        for table in reversed(Base.metadata.sorted_tables):
            con.execute(table.delete())
        sequences = con.execute("SELECT * FROM information_schema.sequences")
        for sequence in sequences:
            sequence_name = sequence[2]
            con.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1")
        trans.commit()


def add_objects(db: Session, objects: Iterable[Base]) -> None:
    for obj in objects:
        db.merge(obj)
    db.commit()


def update_annotators_overall_load(
    db_session: Session, annotators: Iterable[User]
) -> None:
    for annotator in annotators:
        update_user_overall_load(db_session, annotator.user_id)
    db_session.commit()


@pytest.fixture(scope="session")
def use_temp_env_var():
    with patch.dict(os.environ, {"USE_TEST_DB": "1"}):
        yield


@pytest.fixture(scope="module")
def db_session(setup_test_db):
    session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = session_local()

    yield session
    session.close()


@pytest.fixture
def prepare_db_for_ud_task(db_session):
    add_objects(db_session, [CRUD_UD_JOB_1])
    add_objects(
        db_session,
        (CRUD_UD_JOB_2, ManualAnnotationTask(**CRUD_UD_TASK)),
    )
    yield db_session
    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_ud_task_constrains(db_session):
    db_session.add_all(
        [
            *CRUD_UD_CONSTRAINTS_JOBS,
            *CRUD_UD_CONSTRAINTS_FILES,
            *CRUD_UD_CONSTRAINTS_USERS,
            *CRUD_UD_CONSTRAINTS_TASKS,
        ],
    )
    db_session.commit()

    yield db_session
    clear_db()


@pytest.fixture
def prepare_db_for_post_annotation(db_session):
    add_objects(db_session, [POST_ANNOTATION_JOB_1])
    add_objects(
        db_session,
        (
            POST_ANNOTATION_ANNOTATOR,
            POST_ANNOTATION_FILE_1,
            POST_ANNOTATION_PG_TASK_1,
            POST_ANNOTATION_PG_TASK_2,
        ),
    )

    yield db_session
    clear_db()


@pytest.fixture
def prepare_db_for_manifest_creation_with_one_record(db_session):
    add_objects(db_session, [POST_ANNOTATION_JOB_1])
    add_objects(
        db_session,
        (
            POST_ANNOTATION_ANNOTATOR,
            POST_ANNOTATION_FILE_1,
            POST_ANNOTATION_PG_TASK_1,
        ),
    )
    yield db_session
    clear_db()


@pytest.fixture
def prepare_db_for_manifest_creation_with_several_records(db_session, request):
    add_objects(db_session, [POST_ANNOTATION_JOB_1])
    add_objects(
        db_session,
        (
            User(user_id=POST_ANNOTATION_ANNOTATOR.user_id),
            POST_ANNOTATION_ANNOTATOR,
            POST_ANNOTATION_FILE_1,
            POST_ANNOTATION_PG_TASK_1,
            request.param[0],
            request.param[1],
        ),
    )
    yield db_session
    clear_db()


@pytest.fixture
def prepare_db_for_post_annotation_with_existing_doc(db_session):
    add_objects(db_session, [POST_ANNOTATION_JOB_1])
    add_objects(
        db_session,
        (
            POST_ANNOTATION_FILE_1,
            POST_ANNOTATION_PG_TASK_1,
            POST_ANNOTATION_PG_DOC,
        ),
    )

    yield db_session
    clear_db()


@pytest.fixture
def prepare_db_for_construct_doc(prepare_db_for_post_annotation):
    add_objects(prepare_db_for_post_annotation, [POST_ANNOTATION_PG_TASK_2])

    yield prepare_db_for_post_annotation


@pytest.fixture(scope="module")
def prepare_db_for_post(db_session):
    for job in POST_JOBS:
        job_db = Job(**job)
        job_db.annotators = job["annotators"]
        db_session.add(job_db)
    db_session.commit()

    update_annotators_overall_load(db_session, TEST_POST_USERS)

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def moto_s3():
    with mock_s3():
        s3_resource = boto3.resource("s3", region_name=DEFAULT_REGION)
        s3_resource.create_bucket(Bucket=POST_ANNOTATION_PG_DOC.tenant)
        yield s3_resource


@pytest.fixture
def empty_bucket(moto_s3):
    yield moto_s3

    moto_s3.Bucket(POST_ANNOTATION_PG_DOC.tenant).objects.all().delete()


@pytest.fixture
def minio_with_manifest(empty_bucket):
    manifest_path = f"{S3_PATH}/{MANIFEST}"

    empty_bucket.Bucket(POST_ANNOTATION_PG_DOC.tenant).put_object(
        Body=json.dumps(MANIFEST_IN_MINIO), Key=manifest_path
    )
    yield empty_bucket


@pytest.fixture(scope="module")
def prepare_db_for_get_revisions(db_session) -> List[AnnotatedDoc]:
    db_session.add_all([User(user_id=annotator) for annotator in USERS_IDS])
    db_session.commit()
    all_revisions = [AnnotatedDoc(**revision) for revision in REVISIONS[:16]]
    db_session.add_all(all_revisions)
    db_session.commit()

    yield all_revisions

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_get_revisions_similar(
    prepare_db_for_get_revisions: List[AnnotatedDoc],
    db_session,
) -> DocumentLinks:
    similarity_category = Category(
        id="pair_classification",
        name="pair classification",
        type=CategoryTypeSchema.link,
    )
    document_link = DocumentLinks(
        original_doc=prepare_db_for_get_revisions[0],
        similar_doc=prepare_db_for_get_revisions[1],
        label="pair_classification",
    )
    db_session.add(similarity_category)
    db_session.add(document_link)
    db_session.commit()
    yield document_link


@pytest.fixture
def prepare_moto_s3_for_get_revisions():
    with mock_s3():
        s3_resource = boto3.resource("s3", region_name=DEFAULT_REGION)
        s3_resource.create_bucket(Bucket=TEST_TENANT)
        for page_path in PAGES_PATHS:
            s3_resource.Bucket(TEST_TENANT).put_object(
                Body=json.dumps(PAGE),
                Key=page_path,
            )
        yield s3_resource


@pytest.fixture(name="expected_latest_revisions", scope="module")
def load_expected_latest_revisions():
    with open(
        "tests/fixtures/expected_latest_revisions.json", "r"
    ) as json_file:
        json_data = json.load(json_file)
    return json_data


@pytest.fixture(name="expected_all_revisions", scope="module")
def load_expected_all_revisions():
    with open("tests/fixtures/expected_all_revisions.json", "r") as json_file:
        json_data = json.load(json_file)
    return json_data


@pytest.fixture(scope="module")
def prepare_db_for_get_job(db_session):
    db_session.bulk_save_objects(GET_JOBS)
    db_session.commit()
    add_objects(db_session, GET_FILES)
    db_session.bulk_save_objects(JOB_TEST_ANNOTATORS)
    db_session.commit()
    db_session.bulk_save_objects(
        [AnnotatedDoc(**revision) for revision in JOB_TEST_REVISIONS]
    )
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_for_finish_task_status_one_task(db_session):

    add_objects(db_session, [FINISH_TASK_USER_1])
    add_objects(db_session, [FINISH_TASK_JOB_1])
    add_objects(
        db_session,
        (
            FINISH_TASK_FILE_1,
            ManualAnnotationTask(**FINISH_TASK_1),
            ManualAnnotationTask(**FINISH_TASK_2),
            ManualAnnotationTask(**FINISH_TASK_1_SAME_JOB),
            *FINISH_DOCS,
        ),
    )

    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_for_finish_task_with_finish_docs(
    prepare_db_for_finish_task_status_one_task,
):
    db_session = prepare_db_for_finish_task_status_one_task
    add_objects(
        db_session,
        (
            ManualAnnotationTask(**FINISH_TASK_1_SAME_JOB),
            *FINISH_DOCS,
        ),
    )


@pytest.fixture
def prepare_db_for_finish_task_status_two_tasks_same_job(
    prepare_db_for_finish_task_status_one_task,
):
    add_objects(
        prepare_db_for_finish_task_status_one_task,
        [ManualAnnotationTask(**FINISH_TASK_2_SAME_JOB)],
    )

    yield prepare_db_for_finish_task_status_one_task


@pytest.fixture
def prepare_db_for_finish_task_with_not_in_progress_status(
    prepare_db_for_finish_task_status_one_task,
):
    session = prepare_db_for_finish_task_status_one_task
    add_objects(session, [FINISH_TASK_USER_2])
    add_objects(session, [FINISH_TASK_JOB_2])
    add_objects(
        session,
        (
            FINISH_TASK_FILE_2,
            ManualAnnotationTask(**TASK_NOT_IN_PROGRESS_STATUS),
        ),
    )

    yield prepare_db_for_finish_task_status_one_task


@pytest.fixture
def prepare_db_for_finish_task_change_validation_status(
    prepare_db_for_finish_task_status_two_tasks_same_job,
):
    session = prepare_db_for_finish_task_status_two_tasks_same_job
    add_objects(session, [FINISH_TASK_JOB_3])
    tasks_files = [
        ManualAnnotationTask(**task) for task in VALIDATION_TASKS_TO_READY
    ] + [FINISH_TASK_FILE_3]
    add_objects(session, tasks_files)

    yield session


@pytest.fixture
def prepare_db_for_finish_task_failed_validation_status(db_session):
    add_objects(db_session, [FINISH_TASK_JOB_3])
    add_objects(db_session, [FINISH_TASK_FILE_3])

    yield db_session

    clear_db()


@pytest.fixture(scope="function")
def prepare_db_for_finish_task_check_deleted_annotators(db_session):
    add_objects(db_session, [FINISH_TASK_JOB_4])
    add_objects(db_session, [FINISH_TASK_FILE_4])
    tasks = [
        ManualAnnotationTask(**task)
        for task in (
            FINISH_TASK_CHECK_DELETE_USER_ANNOTATOR_1,
            FINISH_TASK_CHECK_DELETE_USER_ANNOTATOR_2,
            FINISH_TASK_CHECK_DELETE_USER_VALIDATOR,
        )
    ]
    add_objects(db_session, tasks)
    add_objects(db_session, FINISH_DOCS_CHECK_DELETED_ANNOTATOR)
    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_categories_same_names(db_session):
    category_tenant = Category(
        id="1", tenant=TEST_TENANT, name="Title", type="box"
    )
    category_common = Category(id="2", tenant=None, name="Table", type="box")
    category_other_tenant = Category(
        id="3", tenant="other_tenant", name="Title", type="box"
    )
    add_objects(
        db_session, (category_tenant, category_common, category_other_tenant)
    )

    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_categories_different_names(db_session):
    category_tenant = Category(
        id="1", tenant=TEST_TENANT, name="Title", type="box"
    )
    category_common = Category(id="2", tenant=None, name="Table", type="box")
    category_other_tenant = Category(
        id="3", tenant="other_tenant", name="Header", type="box"
    )
    categories_all = [category_tenant, category_common, category_other_tenant]
    for cat in categories_all:
        db_session.add(cat)
        db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_categories_for_filtration(db_session):
    category_tenant = Category(
        id="1",
        tenant=TEST_TENANT,
        name="Title",
        type="box",
        tree=sqlalchemy_utils.Ltree("1"),
    )
    category_common = [
        Category(
            id=str(number + 2),
            tenant=None,
            name=f"Table{number}",
            type="box",
            tree=sqlalchemy_utils.Ltree(str(number + 2)),
        )
        for number in range(1, 16)
    ]
    category_other_tenant = Category(
        id="2",
        tenant="other_tenant",
        name="Header",
        type="box",
        tree=sqlalchemy_utils.Ltree("2"),
    )
    for cat in [category_tenant, category_other_tenant, *category_common]:
        db_session.add(cat)
    try:
        db_session.commit()
    except FlushError:
        db_session.rollback()
    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_categories_with_tree(db_session):
    path = ""
    categories = []
    for number in range(1, 16):
        if path:
            path = f"{path}.{number + 2}"
            parent = str(number + 1)
        else:
            path = str(number + 2)
            parent = None
        cat = Category(
            id=str(number + 2),
            tenant="test",
            name=f"Table{number}",
            type="box",
            parent=parent,
            tree=sqlalchemy_utils.Ltree(path),
        )
        categories.append(cat)

    for cat in categories:
        db_session.add(cat)
    try:
        db_session.commit()
    except FlushError:
        db_session.rollback()
    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_categories_for_distinct_filtration(db_session):
    category_editor = Category(
        id="1", tenant=TEST_TENANT, name="Title", editor="person", type="box"
    )
    categories_link = [
        Category(
            id=str(number + 2),
            tenant=None,
            name=f"Table{number}",
            type="link",
        )
        for number in range(2)
    ]
    category_segmentation = Category(
        id="4", tenant=TEST_TENANT, name="Title", type="segmentation"
    )
    for cat in [category_editor, *categories_link, category_segmentation]:
        db_session.add(cat)
    try:
        db_session.commit()
    except FlushError:
        db_session.rollback()
    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_cr_task(db_session):
    db_session.add_all(CRUD_CR_JOBS)
    db_session.commit()
    db_session.add_all([*CRUD_CR_FILES, *CRUD_CR_ANNOTATION_TASKS])
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_update_stats(prepare_db_for_cr_task):
    for task_id in [
        id_
        for (id_,) in prepare_db_for_cr_task.query(
            ManualAnnotationTask.id
        ).all()
    ]:
        add_task_stats_record(
            db=prepare_db_for_cr_task,
            task_id=task_id,
            stats=AnnotationStatisticsInputSchema(event_type="opened"),
        )

    yield prepare_db_for_cr_task
    clear_db()


@pytest.fixture(scope="module")
def prepare_db_update_stats_already_updated(prepare_db_update_stats):
    for task_id in [
        id_
        for (id_,) in prepare_db_update_stats.query(
            ManualAnnotationTask.id
        ).all()
    ]:
        add_task_stats_record(
            db=prepare_db_update_stats,
            task_id=task_id,
            stats=AnnotationStatisticsInputSchema(event_type="opened"),
        )

    yield prepare_db_update_stats
    clear_db()


@pytest.fixture(scope="function")
def prepare_db_for_overall_load(db_session):
    add_objects(db_session, OVERALL_LOAD_JOBS)
    add_objects(
        db_session,
        (
            *OVERALL_LOAD_CREATED_TASKS,
            *TASK_FILES_OVERALL_LOAD,
            VALIDATED_DOC_OVERALL_LOAD,
        ),
    )

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_change_statuses(db_session):
    db_session.add_all(CHANGE_STATUSES_JOBS)
    db_session.commit()
    db_session.add_all(CHANGE_STATUSES_TASKS)
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_post_job(db_session):
    db_session.add(Job(**POST_JOB_EXISTING_JOB))
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_job_for_safe_annotations(db_session):
    job_data = {
        "callback_url": "http://www.test.com/test1",
        "annotators": [],
        "validation_type": ValidationSchema.cross,
        "files": [],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
    }
    for job_id in JOBS_IDS:
        db_session.add(Job(**{**job_data, "job_id": job_id}))
        db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_job_for_get_revision(db_session):
    job_data = {
        "job_id": accumulated_revs.JOB_ID_FOR_ACC_REVISION,
        "callback_url": "http://www.test.com/test1",
        "annotators": [],
        "validation_type": ValidationSchema.cross,
        "files": [],
        "is_auto_distribution": False,
        "categories": CATEGORIES_2,
        "deadline": None,
        "tenant": TEST_TENANT,
    }
    db_session.add(Job(**job_data))
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_get_next_task(db_session):
    db_session.add(NEXT_TASK_JOB)
    db_session.commit()
    db_session.add_all(NEXT_TASK_ANNOTATION_TASKS)
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="function")
def prepare_db_for_batch_delete_tasks(db_session):
    add_objects(db_session, [DELETE_BATCH_TASKS_JOB])
    add_objects(
        db_session, (DELETE_BATCH_TASKS_FILE, DELETE_BATCH_TASKS_ANNOTATOR)
    )
    db_session.bulk_insert_mappings(ManualAnnotationTask, DIFF_STATUSES_TASKS)
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def minio_particular_revision():
    with mock_s3():
        s3_resource = boto3.resource("s3", region_name=DEFAULT_REGION)
        s3_resource.create_bucket(Bucket=TEST_TENANT)

        path = (
            f"{S3_START_PATH}/{PART_REV_DOC.job_id}/"
            f"{PART_REV_DOC.file_id}/"
        )

        s3_resource.Bucket(TEST_TENANT).put_object(
            Body=json.dumps(PART_REV_PAGES[0]),
            Key=path + PART_REV_DOC.pages["1"] + ".json",
        )
        s3_resource.Bucket(TEST_TENANT).put_object(
            Body=json.dumps(PART_REV_PAGES[1]),
            Key=path + PART_REV_DOC.pages["2"] + ".json",
        )

        yield s3_resource


@pytest.fixture(scope="module")
def db_particular_revision(db_session):
    add_objects(db_session, [PART_REV_ANNOTATOR])
    add_objects(db_session, [PART_REV_DOC])

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def db_revisions_without_annotation(db_session):
    add_objects(db_session, [REV_WITHOUT_ANNOTATION_JOB])
    add_objects(
        db_session,
        (
            REV_WITHOUT_ANNOTATION_TASK,
            AnnotatedDoc(**REV_WITHOUT_ANNOTATION_DOC_1),
            AnnotatedDoc(**REV_WITHOUT_ANNOTATION_DOC_2),
            AnnotatedDoc(**REV_WITHOUT_ANNOTATION_DOC_3),
        ),
    )

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def db_get_users_for_job(db_session):
    USERS_FOR_JOB_ANNOTATORS.extend(USERS_FOR_JOB_JOBS)
    db_session.add_all(USERS_FOR_JOB_ANNOTATORS)
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_get_job_files(db_session):
    db_session.add_all(GET_JOB_FILES_JOBS)
    db_session.commit()
    db_session.add_all(GET_JOB_FILES)
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture
def mock_assets_communication(
    monkeypatch, prepare_db_categories_for_filtration
) -> Session:
    monkeypatch.setattr(
        "annotation.jobs.resources.get_files_info",
        Mock(return_value=[{"file_id": MOCK_ID, "pages_number": 2}]),
    )
    return prepare_db_categories_for_filtration


@pytest.fixture
def mock_db_error_for_job_categories(
    monkeypatch, prepare_db_categories_for_filtration
) -> Session:
    monkeypatch.setattr(
        "annotation.jobs.resources.fetch_bunch_categories_db",
        Mock(side_effect=SQLAlchemyError),
    )
    return prepare_db_categories_for_filtration


@pytest.fixture
def mock_db_error_get_job_categories(
    monkeypatch, prepare_db_categories_for_filtration
) -> Session:
    monkeypatch.setattr(
        "annotation.main.filter_job_categories",
        Mock(side_effect=SQLAlchemyError),
    )
    return prepare_db_categories_for_filtration


@pytest.fixture
def prepare_db_job_with_single_category(
    mock_assets_communication,
    request,
) -> Session:
    session = mock_assets_communication
    cat_id = request.param
    categories_db = [session.query(Category).get(cat_id)]
    f = File(file_id=1, tenant=TEST_TENANT, job_id=1, pages_number=1)
    users = [User(user_id=user) for user in CATEGORIES_USERS]
    job = Job(
        job_id=1,
        is_auto_distribution=False,
        callback_url="http://",
        files=[f],
        validation_type=ValidationSchema.cross,
        tenant=TEST_TENANT,
        annotators=users,
        validators=[],
        owners=[],
        categories=categories_db,
    )
    job.categories = categories_db
    session.add(job)
    session.commit()
    yield mock_assets_communication


@pytest.fixture
def prepare_db_job_with_filter_categories(
    mock_assets_communication,
) -> Session:
    session = mock_assets_communication
    categories_db = session.query(Category).filter(Category.id != "2").all()
    f = File(file_id=1, tenant=TEST_TENANT, job_id=1, pages_number=1)
    users = [User(user_id=user) for user in CATEGORIES_USERS]
    job = Job(
        job_id=1,
        is_auto_distribution=False,
        callback_url="http://",
        files=[f],
        validation_type=ValidationSchema.cross,
        tenant=TEST_TENANT,
        annotators=users,
        validators=[],
        owners=[],
        categories=categories_db,
    )
    job.categories = categories_db
    session.add(job)
    session.commit()
    yield mock_assets_communication


@pytest.fixture
def db_annotator_custom_overall_load(db_session, request):
    db_session.add(
        User(user_id=OVERALL_LOAD_USERS[0].user_id, overall_load=request.param)
    )
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture
def db_post_unassigned_files(db_session):
    add_objects(db_session, [JOBS_FILES_TASKS_POST_UN_FILES[0]])
    add_objects(db_session, JOBS_FILES_TASKS_POST_UN_FILES[1:])

    update_annotators_overall_load(db_session, ANNOTATORS_POST_UN_FILES)

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_for_annotation_change_task_statuses(db_session):
    db_session.add_all(
        [
            POST_ANNOTATION_ANNOTATOR,
            POST_ANNOTATION_VALIDATOR,
            POST_ANNOTATION_FILE_1,
            POST_ANNOTATION_VALIDATION_JOB,
            *ANNOTATION_VALIDATION_TASKS_PG,
        ]
    )
    db_session.commit()
    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def db_get_pages_info(db_session):
    db_session.add_all(PAGES_INFO_ENTITIES)
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def db_get_unassigned_files(db_session):
    db_session.add_all(UNASSIGNED_FILES_ENTITIES)
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture
def db_validation_end(db_session):
    add_objects(db_session, [validation.JOBS[0]])
    add_objects(
        db_session, validation.FILES + validation.TASKS + validation.DOCS
    )
    update_annotators_overall_load(db_session, validation.ANNOTATORS)

    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_find_annotators_for_failed_pages(db_validation_end):
    db_validation_end.add(validation.TASK_FAILED_PAGES)
    db_validation_end.commit()
    db_validation_end.add(validation.ANNOTATION_FAILED_PAGES)
    db_validation_end.commit()

    annotator_for_delete = validation.ANNOTATORS[0].user_id

    db_validation_end.query(ManualAnnotationTask).filter(
        ManualAnnotationTask.user_id == annotator_for_delete
    ).delete(synchronize_session=False)
    db_validation_end.commit()
    db_validation_end.query(User).filter(
        User.user_id == annotator_for_delete
    ).delete(synchronize_session=False)
    db_validation_end.commit()

    yield db_validation_end

    clear_db()


@pytest.fixture(scope="module")
def minio_accumulate_revisions(moto_s3):
    path = (
        f"{S3_START_PATH}/{accumulated_revs.JOB_ID_FOR_ACC_REVISION}/"
        f"{accumulated_revs.FILE_ID}/"
    )
    for page_hash, page_annotation in accumulated_revs.PAGES.items():
        moto_s3.Bucket(accumulated_revs.TENANT).put_object(
            Body=json.dumps(page_annotation),
            Key=path + f"{page_hash}.json",
        )

    yield moto_s3


@pytest.fixture(scope="module")
def db_accumulated_revs(db_session):
    add_objects(db_session, accumulated_revs.USERS)
    add_objects(db_session, accumulated_revs.DOCS)

    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_for_update_job(db_session):
    for job in UPDATE_JOBS:
        add_objects(db_session, [job])
    add_objects(
        db_session,
        [
            UPDATE_USER_NO_JOBS,
            *UPDATE_JOB_USERS,
            *UPDATE_JOB_CATEGORIES,
            *UPDATE_JOB_FILES,
        ],
    )
    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def prepare_db_child_categories(db_session):
    add_objects(
        db_session,
        (
            OTHER_TENANT_CHILD_CATEGORY,
            *CYCLIC_TENANT_CHILD_CATEGORIES,
            *COMMON_CHILD_CATEGORIES,
        ),
    )
    last_category_id = CYCLIC_TENANT_CHILD_CATEGORIES[-1].id
    CYCLIC_TENANT_CHILD_CATEGORIES[0].parent = last_category_id  # make cycle
    add_objects(db_session, (CYCLIC_TENANT_CHILD_CATEGORIES[0],))

    yield

    clear_db()


@pytest.fixture
def prepare_db_for_update_job_status(db_session):
    add_objects(db_session, [CHANGE_STATUSES_JOBS[0]])

    yield db_session

    clear_db()


@pytest.fixture
def prepare_child_categories_cache():
    cache.clear()

    yield cache


@pytest.fixture(scope="module")
def prepare_search_annotation_kafka(db_session):
    db_session.add_all(
        [
            ANNOTATION_KAFKA_JOB,
            ANNOTATION_KAFKA_FILE,
            ANNOTATION_KAFKA_TASK,
        ],
    )
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture
def prepare_db_for_get_job_progress(db_session):
    for job in JOBS_TO_TEST_PROGRESS:
        add_objects(db_session, [job])
    db_session.add_all(
        [
            FILE_TEST_PROGRESS,
            *(ManualAnnotationTask(**task) for task in TASKS_TEST_PROGRESS),
        ]
    )
    db_session.commit()

    yield db_session

    clear_db()


@pytest.fixture(scope="module")
def db_get_jobs_info_by_files(db_session):
    add_objects(db_session, jobs_info_by_files.JOBS)

    yield db_session

    clear_db()


@pytest.fixture
def db_errors(request, monkeypatch):
    exception = request.param

    def mock_exception(*args, **kwargs):
        if exception is SQLAlchemyError:
            raise exception
        else:
            raise exception(statement="statement", params={}, orig=None)

    monkeypatch.setattr(Session, "query", mock_exception)


@pytest.fixture
def mock_minio_empty_bucket(monkeypatch, empty_bucket):
    monkeypatch.setattr(
        "annotation.annotations.main.connect_s3",
        Mock(return_value=empty_bucket),
    )
    yield empty_bucket


@pytest.fixture
def prepare_db_with_extensive_coverage_annotations(db_session):
    job = Job(
        # TODO: clean_db() do not clean DB fully. Having static
        #  id causes Exception for tests running after initial
        #   >>> AssertionError: Dependency rule tried to blank-out primary key
        #        column 'files.job_id' on instance '<File at 0x1049e0fa0>'
        job_id=random.randint(1000, 100000),
        callback_url="http://www.test.com/test1",
        annotators=[
            FINISH_TASK_USER_1,
            FINISH_TASK_USER_2,
            FINISH_TASK_USER_3,
        ],
        validators=[FINISH_TASK_USER_3],
        validation_type=ValidationSchema.extensive_coverage,
        files=[FINISH_TASK_FILE_1],
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline=None,
        tenant=TEST_TENANT,
        status=JobStatusEnumSchema.in_progress,
        extensive_coverage=2,
    )
    file = File(
        file_id=10,
        tenant=TEST_TENANT,
        job_id=job.job_id,
        pages_number=9,
        distributed_annotating_pages=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        distributed_validating_pages=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        status=FileStatusEnumSchema.annotated,
    )
    add_objects(db_session, [job, file])
    task_1 = {
        "id": 1,
        "file_id": file.file_id,
        "pages": [1, 2, 3, 4, 9, 8],
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_1.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    }
    task_2 = {
        "id": 2,
        "file_id": file.file_id,
        "pages": [1, 2, 5, 6, 7, 8, 9],
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_2.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    }
    task_3 = {
        "id": 3,
        "file_id": file.file_id,
        "pages": [3, 4, 5, 6, 7],
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_3.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    }
    validation = {
        "id": 4,
        "file_id": file.file_id,
        "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_3.user_id,
        "is_validation": True,
        "status": TaskStatusEnumSchema.pending,
        "deadline": None,
    }

    yield (db_session, (task_1, task_2, task_3), validation)
    clear_db()


@pytest.fixture
def prepare_db_with_extensive_coverage_annotations_same_pages(db_session):
    pages = [_ for _ in range(1, 10)]
    job = Job(
        # TODO: clean_db() do not clean DB fully. Having static
        #  id causes Exception for tests running after initial
        #   >>> AssertionError: Dependency rule tried to blank-out primary key
        #        column 'files.job_id' on instance '<File at 0x1049e0fa0>'
        job_id=random.randint(1000, 100000),
        callback_url="http://www.test.com/test1",
        annotators=[
            FINISH_TASK_USER_1,
            FINISH_TASK_USER_2,
            FINISH_TASK_USER_3,
        ],
        validators=[FINISH_TASK_USER_3],
        validation_type=ValidationSchema.extensive_coverage,
        files=[FINISH_TASK_FILE_1],
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline=None,
        tenant=TEST_TENANT,
        status=JobStatusEnumSchema.in_progress,
        extensive_coverage=2,
    )
    file = File(
        file_id=10,
        tenant=TEST_TENANT,
        job_id=job.job_id,
        pages_number=9,
        distributed_annotating_pages=pages,
        distributed_validating_pages=pages,
        status=FileStatusEnumSchema.annotated,
    )
    add_objects(db_session, [job, file])
    task_1 = {
        "id": 1,
        "file_id": file.file_id,
        "pages": pages,
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_1.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    }
    task_2 = {
        "id": 2,
        "file_id": file.file_id,
        "pages": pages,
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_2.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    }
    task_3 = {
        "id": 3,
        "file_id": file.file_id,
        "pages": pages,
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_3.user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    }
    validation = {
        "id": 4,
        "file_id": file.file_id,
        "pages": pages,
        "job_id": job.job_id,
        "user_id": FINISH_TASK_USER_3.user_id,
        "is_validation": True,
        "status": TaskStatusEnumSchema.pending,
        "deadline": None,
    }

    yield (db_session, (task_1, task_2, task_3), validation)
    clear_db()


@pytest.fixture
def prepare_db_transfer_annotations(db_session):
    add_objects(db_session, [TRANSFER_ANNOTATIONS_FILE])
    add_objects(db_session, [TRANSFER_ANNOTATIONS_JOB])
    add_objects(
        db_session,
        (ManualAnnotationTask(**obj) for obj in TRANSFER_ANNOTATIONS_TASKS),
    )
    add_objects(db_session, [*TRANSFER_ANNOTATIONS_DOCS])
    yield db_session
    clear_db()


@pytest.fixture
def prepare_minio_transfer_annotations(monkeypatch, moto_s3):
    path = (
        f"{S3_START_PATH}/{TRANSFER_ANNOTATIONS_JOB.job_id}/"
        f"{TRANSFER_ANNOTATIONS_FILE.file_id}/"
    )
    for page_hash, page_annotation in TRANSFER_ANNOTATIONS_PAGES.items():
        moto_s3.Bucket(TRANSFER_ANNOTATIONS_JOB.tenant).put_object(
            Body=json.dumps(page_annotation),
            Key=path + f"{page_hash}.json",
        )
    monkeypatch.setattr(
        "annotation.annotations.main.connect_s3",
        Mock(return_value=moto_s3),
    )
    yield moto_s3


@pytest.fixture
def prepare_db_for_redistribute_tasks(db_session):
    add_objects(db_session, [REDISTRIBUTE_TASKS_FILE])
    add_objects(
        db_session,
        [
            REDISTRIBUTE_TASKS_JOB,
            NEW_REDISTRIBUTE_TASKS_CATEGORY,
            NEW_REDISTRIBUTE_TASKS_USER,
        ],
    )
    add_objects(
        db_session,
        (ManualAnnotationTask(**obj) for obj in REDISTRIBUTED_TASKS),
    )
    yield db_session
    clear_db()


# Mock Config Variables #
@pytest.fixture
def assets_host_mock():
    with patch(
        "annotation.microservice_communication."
        "assets_communication.ASSETS_SERVICE_HOST",
        "http://assets:8080"
    ) as assets_host:
        yield assets_host


@pytest.fixture
def assets_url_mock(assets_host_mock):
    with patch(
        "annotation.microservice_communication."
        "assets_communication.ASSETS_URL",
        f"{assets_host_mock}/datasets"
    ) as assets_url:
        yield assets_url


@pytest.fixture
def assets_files_url_mock(assets_host_mock):
    with patch(
        "annotation.microservice_communication."
        "assets_communication.ASSETS_FILES_URL",
        f"{assets_host_mock}/files/search"
    ) as assets_files_url:
        yield assets_files_url


@pytest.fixture
def jobs_host_mock():
    with patch(
        "annotation.microservice_communication."
        "jobs_communication.JOBS_SERVICE_HOST",
        "http://jobs:8080"
    ) as jobs_host:
        yield jobs_host


@pytest.fixture
def jobs_search_url_mock(jobs_host_mock):
    with patch(
        "annotation.microservice_communication."
        "jobs_communication.JOBS_SEARCH_URL",
        f"{jobs_host_mock}/jobs/search"
    ) as jobs_search_url:
        yield jobs_search_url
