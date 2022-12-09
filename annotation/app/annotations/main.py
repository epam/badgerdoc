import json
import os
from datetime import datetime
from hashlib import sha1
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

import boto3
from dotenv import find_dotenv, load_dotenv
from fastapi import HTTPException
from kafka import KafkaProducer
from kafka.errors import KafkaError
from sqlalchemy import asc
from sqlalchemy.orm import Session

from app import logger
from app.kafka_client import KAFKA_BOOTSTRAP_SERVER, KAFKA_SEARCH_TOPIC
from app.kafka_client import producers as kafka_producers
from app.models import AnnotatedDoc
from app.schemas import (
    AnnotatedDocSchema,
    DocForSaveSchema,
    PageSchema,
    ParticularRevisionSchema,
)

load_dotenv(find_dotenv())
ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_PREFIX = os.environ.get("S3_PREFIX")
AWS_ACCESS_KEY_ID = os.environ.get("S3_LOGIN")
AWS_SECRET_ACCESS_KEY = os.environ.get("S3_PASS")
INDEX_NAME = os.environ.get("INDEX_NAME")
S3_START_PATH = os.environ.get("S3_START_PATH")
S3_CREDENTIALS_PROVIDER = os.environ.get("S3_CREDENTIALS_PROVIDER")
MANIFEST = "manifest.json"
LATEST = "latest"


logger_ = logger.Logger
logger_.debug("S3_PREFIX: %s", S3_PREFIX)


def row_to_dict(row) -> dict:
    if hasattr(row, "__table__"):
        return {
            column.key: (
                str(row.__getattribute__(column.key))
                if isinstance(row.__getattribute__(column.key), UUID)
                else row.__getattribute__(column.key).isoformat()
                if isinstance(row.__getattribute__(column.key), datetime)
                else row.__getattribute__(column.key)
            )
            for column in row.__table__.columns
            if column.key != "_sa_instance_state"
        }
    return {
        key: (
            str(value)
            if isinstance(value, UUID)
            else value.isoformat()
            if isinstance(value, datetime)
            else value
        )
        for key, value in row.__dict__.items()
        if key != "_sa_instance_state"
    }


def convert_bucket_name_if_s3prefix(bucket_name: str) -> str:
    if S3_PREFIX:
        return f"{S3_PREFIX}-{bucket_name}"
    else:
        return bucket_name


class NotConfiguredException(Exception):
    pass


def connect_s3(bucket_name: str) -> boto3.resource:
    boto3_config = {}
    if S3_CREDENTIALS_PROVIDER == "minio":
        boto3_config.update(
            {
                "aws_access_key_id": AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
                "endpoint_url": ENDPOINT_URL,
            }
        )
    elif S3_CREDENTIALS_PROVIDER == "aws_iam":
        # No additional updates to config needed - boto3 uses env vars
        ...
    else:
        raise NotConfiguredException(
            "s3 connection is not properly configured - "
            "s3_credentials_provider is not set"
        )
    s3_resource = boto3.resource("s3", **boto3_config)
    logger_.debug(f"S3_Credentials provider - {S3_CREDENTIALS_PROVIDER}")

    try:
        logger_.debug("Connecting to S3 bucket: %s", bucket_name)
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
        # here is some bug or I am missing smth: this line ^
        # should raise NoSuchBucket
        # error, if bucket is not available, but for some reason
        # it responses with TypeError: NoneType object is not
        # callable, this try/except block should be changed after understanding
        # what is going on
    except TypeError:
        raise s3_resource.meta.client.exceptions.NoSuchBucket
    return s3_resource


def upload_pages_to_minio(
    pages: List[PageSchema],
    pages_sha: Dict[str, str],
    s3_path: str,
    bucket_name: str,
    s3_resource: boto3.resource,
) -> None:
    """
    Upload given list of pages to minio.
    :param pages: list of pages with annotations
    :param pages_sha: dict of page nums and pages hash
        structure: {{page_num}: {page_hash}, ...}
    :param s3_path: start path for saving annotations in minio
        structure: annotation/{job_id}/{file_id}
    :param tenant: name of bucket, where annotations should be saved
    :param s3_resource: opened minio connection
    :return: None
    """
    for page in pages:
        json_page = json.dumps(page.dict())
        path_to_object = f"{s3_path}/{pages_sha[str(page.page_num)]}.json"
        upload_json_to_minio(
            json_page, path_to_object, bucket_name, s3_resource
        )


def upload_json_to_minio(
    json_obj: str,
    path_to_object: str,
    bucket_name: str,
    s3_resource: boto3.resource,
) -> None:
    """
    Upload json to minio in bucket with name equal to tenant.
    :param json_obj: json, derived from dict
    :param path_to_object: full minio path for annotation save
        structure: annotation/{job_id}/{file_id}/{page_hash}.json
    :param tenant: name of bucket, where annotations should be saved
    :param s3_resource: opened minio connection
    :return: None
    """
    s3_resource.Bucket(bucket_name).put_object(
        Body=json_obj,
        Key=path_to_object,
    )


def get_sha_of_bytes(b_page: bytes) -> str:
    return sha1(b_page).hexdigest()


def get_pages_sha(
    pages: List[PageSchema],
    base_revision: Optional[str],
    validated: Set[int],
    failed: Set[int],
) -> Tuple[Dict[str, str], str]:
    """
    Creates dict:
    key: page_num of page from given array,
    key: sha of page from given array
    Calculates sha for every page in given array and adds it to dict.
    Calculates sha of:
    string sha from base revision + concatenated pages + validated array
    + failed array
    Returns tuple of dict and hexdigest of concatenated sha.
    """

    pages_sha = {}

    if base_revision is None:
        b_pages = b""
    else:
        b_pages = base_revision.encode()

    for page in pages:
        json_page = json.dumps(page.dict())
        b_page = json_page.encode()
        b_pages += b_page

        str_page_num = str(page.page_num)
        pages_sha[str_page_num] = get_sha_of_bytes(b_page)

    b_pages += json.dumps(sorted(list(validated))).encode()
    b_pages += json.dumps(sorted(list(failed))).encode()

    concatenated_pages_sha = get_sha_of_bytes(b_pages)

    return pages_sha, concatenated_pages_sha


def create_manifest_json(
    doc: AnnotatedDoc,
    s3_path: str,
    s3_file_path: Optional[str],
    s3_file_bucket: Optional[str],
    bucket_name: str,
    job_id: int,
    file_id: int,
    doc_categories: Optional[List[str]],
    db: Session,
    s3_resource: boto3.resource,
) -> None:
    """
    Gets revisions belonging to job_id and file_id sorted by date.
    Creates manifest by path annotation/{job_id}/{file_id} and
    adds to manifest pages with hashes of only latest revisions.
    If manifest already exists - rewrites it.
    """
    manifest_path = f"{s3_path}/{MANIFEST}"

    revisions = (
        db.query(AnnotatedDoc)
        .filter(AnnotatedDoc.file_id == file_id, AnnotatedDoc.job_id == job_id)
        .order_by(asc(AnnotatedDoc.date))
        .all()
    )
    revisions.append(doc)
    validated, failed_validation, all_pages, *_ = accumulate_pages_info(
        [], revisions, with_page_hash=True
    )
    manifest = row_to_dict(doc)
    redundant_keys = ("task_id", "file_id", "tenant")
    manifest = {
        key: value
        for key, value in manifest.items()
        if key not in redundant_keys
    }
    manifest["pages"] = all_pages
    manifest["validated"] = list(validated)
    manifest["failed_validation_pages"] = list(failed_validation)
    manifest["file"] = s3_file_path
    manifest["bucket"] = s3_file_bucket
    manifest["categories"] = doc_categories

    manifest_json = json.dumps(manifest)
    upload_json_to_minio(
        manifest_json, manifest_path, bucket_name, s3_resource
    )


def construct_annotated_doc(
    db: Session,
    user_id: Optional[UUID],
    pipeline_id: Optional[int],
    job_id: int,
    file_id: int,
    doc: DocForSaveSchema,
    tenant: str,
    s3_file_path: Optional[str],
    s3_file_bucket: Optional[str],
    latest_doc: Optional[AnnotatedDoc],
    task_id: Optional[int],
    is_latest: bool,
) -> AnnotatedDoc:
    """
    Try to create new revision and upload annotations to minio, if needed.
    If is_latest flag is True, given base revision is latest,
    there is not merge conflict, pages dict will consist
    only of pages dict from new revision.
    If is_latest flag is False, given base revision is not latest,
    there is merge conflict, pages dict will consist of
    pages dict from the latest revision and new revision.
    In both cases dict with hash for every page is calculated,
    hash is used in page name in minio,
    also this dict is stored as attribute `pages` of revision.
    To get revision id following calculations should be performed:
        hash of concatenation of:
        previous revision id + concatenated pages hash +
        hash of validated array + hash of failed validation pages array
    If pages dict, validated array and failed validation pages array are
    equal in previous and new revisions, new revision will not be created,
    function will return the latest revision,
    annotations will not be uploaded to minio,
    manifest will not be overwritten.
    Otherwise, new revision will be returned, annotations will be
    uploaded to minio and new manifest will be created and uploaded to
    minio as well.
    :param db: SQLAlchemy session
    :param user_id: user, who wants to save revision and annotations,
        if pipeline is saving, this field must be None
    :param pipeline_id: pipeline, that wants to save revision and annotations,
        if user is saving, this field must be None
    :param job_id: id of job, where saving is performed
    :param file_id: id of file, for which saving is performed
    :param doc: derived request body
    :param tenant: bucket, where annotations will be saved
    :param s3_file_path: file path, where given file is stored,
        this info is derived from assets service and
        used only to store it in manifest
    :param s3_file_bucket: name of bucket, where given file is stored,
        this info is derived from assets service and
        used only to store it in manifest
    :param latest_doc: latest revision from db
    :param task_id: id of task, within which saving is performed,
        if pipeline is saving, this field must be None
    :param is_latest: flag, that indicated, if given base_revision is latest
        or not. If flag is False, merge conflict will occur
    :return: newly created revision or latest revision
    """
    annotated_doc = AnnotatedDoc(
        user=user_id,
        pipeline=pipeline_id,
        file_id=file_id,
        job_id=job_id,
        validated=doc.validated,
        failed_validation_pages=doc.failed_validation_pages,
        tenant=tenant,
        task_id=task_id,
    )
    s3_path = f"{S3_START_PATH}/{str(job_id)}/{str(file_id)}"

    if is_latest:
        # if is_latest flag is True, it means,
        # that given base revision is latest,
        # hence no merge conflicts
        pages_sha, concatenated_pages_sha = get_pages_sha(
            doc.pages,
            doc.base_revision,
            doc.validated,
            doc.failed_validation_pages,
        )
        annotated_doc.pages = pages_sha
        annotated_doc.revision = concatenated_pages_sha
    else:
        # merge conflict
        # for new annotated doc
        # base revision will be latest revision from db,
        # pages array will consist of given pages +
        # pages from latest revision from db
        pages_sha, concatenated_pages_sha = get_pages_sha(
            doc.pages,
            latest_doc.revision,
            doc.validated,
            doc.failed_validation_pages,
        )
        annotated_doc.pages = pages_sha
        annotated_doc.pages.update(latest_doc.pages)
        annotated_doc.revision = concatenated_pages_sha

    if check_docs_identity(
        latest_doc=latest_doc,
        new_doc=annotated_doc,
    ):
        return latest_doc

    db.add(annotated_doc)
    db.flush()

    bucket_name = convert_bucket_name_if_s3prefix(tenant)
    s3_resource = connect_s3(bucket_name)
    upload_pages_to_minio(
        pages=doc.pages,
        pages_sha=pages_sha,
        s3_path=s3_path,
        bucket_name=bucket_name,
        s3_resource=s3_resource,
    )
    create_manifest_json(
        annotated_doc,
        s3_path,
        s3_file_path,
        s3_file_bucket,
        bucket_name,
        job_id,
        file_id,
        doc.categories,
        db,
        s3_resource,
    )

    return annotated_doc


def check_docs_identity(
    latest_doc: AnnotatedDoc,
    new_doc: AnnotatedDoc,
) -> bool:
    """
    Check if fields 'pages', 'validated' and 'failed_validation_pages'
    are equal in the latest_doc (revision) in db and in new_doc (revision).
    If they are equal, new_doc (revision) will not be committed to db,
    in response user will get latest revision from db.
    :param latest_doc: latest doc in db
    :param new_doc: new doc, that currently being constructed
    :return: True if latest_doc is present in db and revisions are equal,
    otherwise False
    """
    return (
        latest_doc is not None
        and latest_doc.pages == new_doc.pages
        and set(latest_doc.validated) == new_doc.validated
        and set(latest_doc.failed_validation_pages)
        == new_doc.failed_validation_pages
    )


def update_pages_array(
    old_pages_to_add: Set[int],
    new_pages_to_add: Set[int],
    new_pages_to_remove: Set[int],
) -> Set[int]:
    """
    Construct set of validated of failed pages.
    For constructing validated array:
    1) old_pages_to_add set should contain validated pages from
    previous revision
    2) new_pages_to_add set should contain validated pages from
    new revision
    3) new_pages_to_remove set should contain failed pages from
    new revision
    Same logic for constructing failed pages set.
    For example:
    Sets from previous revision:
        set of validated = {1, 2, 3}
        set of failed = {4, 5}
    Sets from new revision:
        set of validated = {4}
        set of failed = {1, 2}
    In result:
        set of validated = {1, 2, 3} + {4} - {1, 2} = {3, 4}
        set of failed = {4, 5} + {1, 2} - {4} = {1, 2, 5}
    """
    old_pages_to_add.update(new_pages_to_add)
    return old_pages_to_add - new_pages_to_remove


def check_if_kafka_message_is_needed(
    db: Session,
    latest_doc: AnnotatedDoc,
    new_doc: AnnotatedDoc,
    job_id: int,
    file_id: int,
    tenant: str,
) -> None:
    if latest_doc != new_doc:
        db.commit()
        send_annotation_kafka_message(job_id, file_id, tenant)


PageRevision = Dict[str, Union[Optional[str], datetime, bool]]


def mark_all_revisions_validated_pages(
    pages: Dict[int, List[PageRevision]],
    revision: AnnotatedDocSchema,
    page_numbers: Set[int],
):
    revision.validated = [
        page_num for page_num in revision.validated if page_num in page_numbers
    ]
    for page_num in revision.validated:
        page_revisions = pages.get(page_num, [])
        validated_pages = [
            page for page in page_revisions if page["user_id"] == revision.user
        ]
        if validated_pages:
            validated_pages[-1]["is_validated"] = True
        else:
            pages.setdefault(page_num, []).append(
                {
                    "user_id": revision.user,
                    "pipeline": revision.pipeline,
                    "job_id": revision.job_id,
                    "file_id": revision.file_id,
                    "revision": revision.revision,
                    "page_id": None,
                    "date": revision.date,
                    "is_validated": True,
                }
            )


LatestPageRevision = Dict[Optional[str], Union[Optional[str], datetime, bool]]


def mark_latest_revision_validated_pages(
    pages: Dict[int, Dict[str, LatestPageRevision]],
    revision: AnnotatedDocSchema,
    page_numbers: Set[int],
):
    revision.validated = [
        page_num for page_num in revision.validated if page_num in page_numbers
    ]
    for page_num in revision.validated:
        try:
            pages[page_num][revision.user]["is_validated"] = True
        except KeyError:
            pages.setdefault(page_num, {})[revision.user] = {
                "pipeline": revision.pipeline,
                "job_id": revision.job_id,
                "file_id": revision.file_id,
                "revision": revision.revision,
                "page_id": None,
                "date": revision.date,
                "is_validated": True,
            }


def find_all_revisions_pages(
    revisions: List[AnnotatedDoc],
    page_numbers: Set[int],
) -> Dict[int, List[PageRevision]]:
    """
    pages structure:
    {
        page_number_1: [
            {
                "user_id": "int",
                "pipeline": "int",
                "job_id": "int",
                "file_id": "int",
                "revision": "sha1",
                "page_id": "sha1",
                "date": "datetime",
                "is_validated": bool,
            },
            ...
        ],
        page_number_2: [...],
        ...
    }
    """
    pages = {}
    revisions = [
        AnnotatedDocSchema.from_orm(revision) for revision in revisions
    ]
    for revision in revisions:
        revision.pages = {
            int(key): value
            for key, value in revision.pages.items()
            if int(key) in page_numbers
        }
        for page_num, page_id in revision.pages.items():
            pages.setdefault(page_num, []).append(
                {
                    "user_id": revision.user,
                    "pipeline": revision.pipeline,
                    "job_id": revision.job_id,
                    "file_id": revision.file_id,
                    "revision": revision.revision,
                    "page_id": page_id,
                    "date": revision.date,
                    "is_validated": False,
                }
            )
        mark_all_revisions_validated_pages(pages, revision, page_numbers)
    return pages


def find_latest_revision_pages(
    revisions: List[AnnotatedDoc],
    page_numbers: Set[int],
) -> Dict[int, Dict[str, LatestPageRevision]]:
    """
    pages structure:
    {
        page_number_1: {
            "user_id_1": {
                "pipeline": "int"
                "job_id": "int",
                "file_id": "int",
                "revision": "sha1",
                "page_id": "sha1",
                "date": "datetime",
                "is_validated": bool,
            },
            "user_id_2": {...},
            ...
        }
        page_number_2: {...},
        ...
    }
    """
    pages = {}
    revisions = [
        AnnotatedDocSchema.from_orm(revision) for revision in revisions
    ]
    for revision in revisions:
        revision.pages = {
            int(key): value
            for key, value in revision.pages.items()
            if int(key) in page_numbers
        }
        for page_num, page_id in revision.pages.items():
            pages.setdefault(page_num, {})[revision.user] = {
                "pipeline": revision.pipeline,
                "job_id": revision.job_id,
                "file_id": revision.file_id,
                "revision": revision.revision,
                "page_id": page_id,
                "date": revision.date,
                "is_validated": False,
            }
        mark_latest_revision_validated_pages(pages, revision, page_numbers)
    return pages


LoadedPage = Dict[
    str,
    Union[
        List[Optional[dict]],
        List[float],
        Optional[str],
        int,
        datetime,
        bool,
    ],
]


def load_page(
    s3_resource: boto3.resource,
    loaded_pages: List[Optional[LoadedPage]],
    bucket_name: str,
    page_num: int,
    user_id: str,
    page_revision: PageRevision,
    is_not_particular_revision_page: bool,
):
    if page_revision["page_id"]:
        page_path = (
            f"{S3_START_PATH}/{page_revision['job_id']}/"
            f"{page_revision['file_id']}/{page_revision['page_id']}"
            ".json"
        )
        page_obj = s3_resource.Object(bucket_name, page_path)
        loaded_page = json.loads(page_obj.get()["Body"].read().decode("utf-8"))
    else:
        loaded_page = {
            "page_num": page_num,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [],
        }
    if is_not_particular_revision_page:
        loaded_page["revision"] = page_revision["revision"]
        loaded_page["page_num"] = page_num
        loaded_page["user_id"] = user_id
        loaded_page["pipeline"] = page_revision["pipeline"]
        loaded_page["date"] = page_revision["date"]
        loaded_page["is_validated"] = page_revision["is_validated"]
    loaded_pages.append(loaded_page)


def get_file_manifest(
    job_id: str, file_id: str, tenant: str, s3_resource: boto3.resource
) -> Dict[str, Any]:
    manifest_path = f"{S3_START_PATH}/{job_id}/{file_id}/{MANIFEST}"
    bucket_name = convert_bucket_name_if_s3prefix(tenant)
    manifest_obj = s3_resource.Object(bucket_name, manifest_path)
    return json.loads(manifest_obj.get()["Body"].read().decode("utf-8"))


def load_all_revisions_pages(
    pages: Dict[int, List[PageRevision]],
    tenant: str,
):
    bucket_name = convert_bucket_name_if_s3prefix(tenant)
    s3_resource = connect_s3(bucket_name)
    for page_num, page_revisions in pages.items():
        loaded_pages = []
        for page_revision in page_revisions:
            load_page(
                s3_resource,
                loaded_pages,
                bucket_name,
                page_num,
                page_revision["user_id"],
                page_revision,
                True,
            )
        pages[page_num] = loaded_pages


def load_latest_revision_pages(
    pages: Dict[int, Dict[str, LatestPageRevision]],
    tenant: str,
):
    bucket_name = convert_bucket_name_if_s3prefix(tenant)
    s3_resource = connect_s3(bucket_name)
    for page_num, page_revisions in pages.items():
        loaded_pages = []
        for user_id, page_revision in page_revisions.items():
            load_page(
                s3_resource,
                loaded_pages,
                bucket_name,
                page_num,
                user_id,
                page_revision,
                True,
            )
        pages[page_num] = loaded_pages


def load_annotated_pages_for_particular_rev(
    revision: AnnotatedDoc,
    page_revision: PageRevision,
    s3_resource: boto3.resource,
    loaded_pages: List[Optional[LoadedPage]],
) -> None:
    """
    Loads annotation of revision`s pages from minIO.
    """
    for page_num, page_id in revision.pages.items():
        page_revision["page_id"] = page_id
        bucket_name = convert_bucket_name_if_s3prefix(revision.tenant)
        load_page(
            s3_resource,
            loaded_pages,
            bucket_name,
            page_num,
            revision.user,
            page_revision,
            False,
        )


def load_validated_pages_for_particular_rev(
    revision: AnnotatedDoc,
    page_revision: PageRevision,
    s3_resource: boto3.resource,
    loaded_pages: List[Optional[LoadedPage]],
) -> None:
    """
    For validated pages, that do not
    have annotation, function sets empty
    annotation (see `load_page` function).
    """
    for page_num in revision.validated:
        if str(page_num) not in revision.pages:
            page_revision["page_id"] = None
            bucket_name = convert_bucket_name_if_s3prefix(revision.tenant)
            load_page(
                s3_resource,
                loaded_pages,
                bucket_name,
                page_num,
                revision.user,
                page_revision,
                False,
            )


def construct_particular_rev_response(
    revision: AnnotatedDoc,
) -> ParticularRevisionSchema:
    """
    Finds annotation of revision`s pages in minIO
    and returns it.
    Example:
    {
      "revision": "b3816722cf3489bc5a97d1e7f085bff5be114da5",
      "user": null,
      "pipeline": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "date": "2021-10-29T13:46:30.973845",
      "pages": [
        {
          "page_num": 1,
          "size": {"width": 0.0, "height": 0.0},
          "objs": [...],
        }
      ],
      "validated": [1],
      "failed_validation_pages": [],
    }
    """
    bucket_name = convert_bucket_name_if_s3prefix(revision.tenant)
    s3_resource = connect_s3(bucket_name)

    page_revision = {
        "job_id": revision.job_id,
        "file_id": revision.file_id,
    }
    loaded_pages = []

    load_annotated_pages_for_particular_rev(
        revision, page_revision, s3_resource, loaded_pages
    )
    load_validated_pages_for_particular_rev(
        revision, page_revision, s3_resource, loaded_pages
    )
    manifest = get_file_manifest(
        str(revision.job_id),
        str(revision.file_id),
        revision.tenant,
        s3_resource,
    )
    doc_categories = manifest.get("categories")
    particular_rev = ParticularRevisionSchema(
        revision=revision.revision,
        user=revision.user,
        pipeline=revision.pipeline,
        date=revision.date,
        pages=loaded_pages,
        validated=revision.validated,
        failed_validation_pages=revision.failed_validation_pages,
        categories=doc_categories,
    )
    return particular_rev


def check_null_fields(doc: DocForSaveSchema) -> None:
    if not doc.pages:
        doc.pages = []
    if not doc.validated:
        doc.validated = set()
    if not doc.failed_validation_pages:
        doc.failed_validation_pages = set()


def accumulate_pages_info(
    task_pages: List[int],
    revisions: List[AnnotatedDoc],
    stop_revision: str = None,
    specific_pages: Set[int] = None,
    with_page_hash: bool = False,
) -> Tuple[Set[int], Set[int], Set[int], Set[int], Optional[AnnotatedDoc]]:
    """
    Get pages, that have been validated, marked as failed, annotated and
    not processed in all given revisions (revisions are sorted in asc order).
    If there are specific pages, function will accumulate info only about
    these pages.
    if with_page_hash param is True, info about page nums and their hash will
    be accumulated, otherwise info only about annotated page nums
    """
    validated = set()
    failed = set()
    annotated = {} if with_page_hash else set()
    required_revision = None

    for revision in revisions:
        validated = update_pages_array(
            old_pages_to_add=validated,
            new_pages_to_add=set(revision.validated)
            if specific_pages is None
            else set(revision.validated).intersection(specific_pages),
            new_pages_to_remove=set(revision.failed_validation_pages)
            if specific_pages is None
            else set(revision.failed_validation_pages).intersection(
                specific_pages
            ),
        )

        failed = update_pages_array(
            old_pages_to_add=failed,
            new_pages_to_add=set(revision.failed_validation_pages)
            if specific_pages is None
            else set(revision.failed_validation_pages).intersection(
                specific_pages
            ),
            new_pages_to_remove=set(revision.validated)
            if specific_pages is None
            else set(revision.validated).intersection(specific_pages),
        )

        if with_page_hash:
            pages = (
                set(revision.pages)
                if specific_pages is None
                else set(map(str, specific_pages))
            )
            for page in pages:
                page_hash = revision.pages.get(page)
                if page_hash is not None:
                    annotated[page] = page_hash
        else:
            annotated.update(set(map(int, revision.pages)))

        # if there is specific revision, where we need to stop,
        # we will stop here
        if stop_revision is not None and revision.revision == stop_revision:
            required_revision = revision
            break

    else:
        if stop_revision == LATEST:
            required_revision = revisions[-1]
        elif stop_revision is not None:
            # required revision id was not found
            required_revision = None

    not_processed = (
        set(sorted(task_pages))
        .difference(annotated)
        .difference(failed)
        .difference(validated)
    )

    return validated, failed, annotated, not_processed, required_revision


def check_task_pages(
    pages: List[PageSchema],
    validated: Set[int],
    failed: Set[int],
    task_pages: Set[int],
) -> None:
    """
    Check, that pages from revision belong to
    the task.
    :param pages: annotated pages from revision
    :param validated: validated pages from revision
    :param failed: failed pages from revision
    :param task_pages: pages, which belong to
    the task
    """
    extra_validated = validated.difference(task_pages)
    extra_failed = failed.difference(task_pages)
    extra_pages = {page.page_num for page in pages}.difference(task_pages)

    err_msg = ""

    error_mapping = {
        "validated": extra_validated,
        "failed": extra_failed,
        "pages": extra_pages,
    }

    for array_name, pgs in error_mapping.items():
        if pgs:
            err_msg += (
                f"Pages {pgs} from {array_name} array "
                "do not belong to the task. "
            )

    if err_msg:
        raise HTTPException(
            status_code=400,
            detail=err_msg,
        )


def _init_search_annotation_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
            client_id="search_group",
            value_serializer=lambda m: json.dumps(m).encode("utf8"),
        )
        return producer
    except KafkaError as error:  # KafkaError is parent of all kafka errors
        logger_.warning(
            f"Error occurred during kafka producer creating: {error}"
        )


def add_search_annotation_producer() -> KafkaProducer:
    search_annotation_producer = _init_search_annotation_producer()
    kafka_producers["search_annotation"] = search_annotation_producer
    return search_annotation_producer


def send_annotation_kafka_message(
    job_id: int, file_id: int, tenant: str
) -> None:
    # if startup failed, try to recreate it
    search_annotation_producer = (
        kafka_producers.get("search_annotation")
        or add_search_annotation_producer()
    )
    if search_annotation_producer:
        search_annotation_producer.send(
            topic=KAFKA_SEARCH_TOPIC,
            value={
                "job_id": job_id,
                "file_id": file_id,
                "tenant": tenant,
            },
        )
