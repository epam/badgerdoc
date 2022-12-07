import json
from typing import Iterator, Optional

import boto3
from botocore.errorfactory import ClientError
from elasticsearch import helpers

import search.es as es
import search.schemas as schemas
from search.config import settings
from search.logger import logger


def convert_bucket_name_if_s3prefix(bucket_name: str) -> str:
    if settings.s3_prefix:
        return f"{settings.s3_prefix}-{bucket_name}"
    else:
        return bucket_name


class NotConfiguredException(Exception):
    pass


def create_boto3_config():
    boto3_config = {}
    if settings.s3_credentials_provider == "minio":
        boto3_config.update(
            {
                "aws_access_key_id": settings.s3_login,
                "aws_secret_access_key": settings.s3_pass,
                "endpoint_url": settings.s3_endpoint_url,
            }
        )
    elif settings.s3_credentials_provider == "aws_iam":
        # No additional updates to config needed - boto3 uses env vars
        ...
    else:
        raise NotConfiguredException(
            "s3 connection is not properly configured "
            "- s3_credentials_provider is not set"
        )
    logger.info(
        f"S3_Credentials provider - {settings.s3_credentials_provider}")
    return boto3_config


def connect_s3(tenant: str) -> boto3.resource:
    boto3_config = create_boto3_config()
    s3_resource = boto3.resource("s3", **boto3_config)
    try:
        s3_resource.meta.client.head_bucket(Bucket=tenant)
    except ClientError as err:
        if "404" in err.args[0]:
            raise es.NoSuchTenant(f"Bucket for tenant {tenant} doesn't exist")
    return s3_resource


def parse_json(
    text_piece_object: list,
    job_id: int,
    file_id: str,
    page_num: str,
    tenant: str,
) -> Optional[Iterator[dict]]:
    if isinstance(text_piece_object, list):
        for text_piece in text_piece_object:
            try:
                content = text_piece["text"]
            except KeyError:
                continue
            document_params = content, job_id, int(file_id), int(page_num)
            if content:
                text_piece = prepare_es_document(text_piece, *document_params)
                yield {"_index": tenant, "_source": text_piece.dict()}
    else:
        logger.warning("Given object is not of type list")


def prepare_es_document(
    document: dict, content: str, job: int, file: int, page: int
) -> schemas.pieces.GeomObject:
    es_document = dict(
        document_id=file,
        page_number=page,
        content=content,
        job_id=job,
    )
    es_document["category"] = document["category"]
    es_document["bbox"] = document.get("bbox")
    es_document["tokens"] = document.get("tokens")
    return schemas.pieces.GeomObject.parse_obj(
        es_document
    )  # for input data validation


def extract_manifest_data(
    s3: boto3.resource, tenant: str, job: int, file: str, object_data: str
) -> dict:
    pages = json.loads(object_data)["pages"]
    file_path = f"{settings.s3_start_path}/{job}/{file}"
    for page_num, page_file in pages.items():
        page_obj = s3.Object(tenant, f"{file_path}/{page_file}.json")
        page_data = json.loads(page_obj.get()["Body"].read().decode("utf-8"))
        geom_objects = page_data["objs"]
        pages[page_num] = geom_objects
    return pages


def harvester(
    tenant: str, job_id: int, file_id: Optional[int] = None
) -> Optional[Iterator[dict]]:
    bucket_name = convert_bucket_name_if_s3prefix(tenant)
    s3 = connect_s3(bucket_name)

    if file_id is None:
        prefix = f"{settings.s3_start_path}/{job_id}"
    else:
        prefix = f"{settings.s3_start_path}/{job_id}/{file_id}"

    for bucket_object in s3.Bucket(bucket_name).objects.filter(Prefix=prefix):
        if not bucket_object.key.endswith(settings.manifest):
            continue
        object_data = bucket_object.get()["Body"].read().decode("utf-8")
        file_id = bucket_object.key.split("/")[-2]
        pages_objects = extract_manifest_data(
            s3, bucket_name, job_id, file_id, object_data
        )
        for page_num, text_piece_object in pages_objects.items():
            yield from parse_json(
                text_piece_object,
                job_id,
                file_id,
                page_num,
                tenant,
            )


async def old_pieces_cleaner(
    tenant: str, job_id: int, file_id: Optional[int] = None
) -> Optional[Iterator[dict]]:
    await es.prepare_index(es.ES, tenant)

    if file_id is None:
        es_query = {"query": {"term": {"job_id": job_id}}}
    else:
        es_query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"job_id": job_id}},
                        {"term": {"document_id": file_id}},
                    ]
                }
            }
        }

    objects_to_delete = helpers.async_scan(
        es.ES,
        query=es_query,
        index=tenant,
        _source=False,
        track_scores=False,
    )
    async for es_object in objects_to_delete:
        es_object["_op_type"] = "delete"
        es_object.pop("_type")
        yield es_object


async def start_harvester(
    tenant: str, job_id: int, file_id: Optional[int] = None
) -> None:
    await helpers.async_bulk(
        es.ES, old_pieces_cleaner(tenant, job_id, file_id)
    )
    await helpers.async_bulk(es.ES, harvester(tenant, job_id, file_id))
