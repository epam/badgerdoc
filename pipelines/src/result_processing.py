from __future__ import annotations

import json
from collections import defaultdict
from json import JSONDecodeError
from typing import Any, Dict, List, Optional, Tuple, Union

import urllib3.exceptions
from minio import Minio
from minio import error as minioerr
from pydantic import BaseModel, ValidationError

from src import config, http_utils, log

logger = log.get_logger(__file__)


class ModelOutput(BaseModel):
    """Class to store model output."""

    pages: List[Page]

    @staticmethod
    def merge(results: List[ModelOutput]) -> Optional[ModelOutput]:
        """Merge results into one.

        :param results: Results to merge.
        :return: Merged results if succeeded.
        """
        pages = [page for result in results for page in result.pages]
        grouped_pages = Page.group_pages_by_page_num(pages).values()
        merged_pages = [Page.merge(pages_) for pages_ in grouped_pages]
        if not merged_pages:
            logger.error("result for merged pages is None")
            return None
        return ModelOutput(pages=merged_pages)

    @staticmethod
    def parse_models(
        raw_data: Union[List[bytes], List[str]]
    ) -> Optional[List[ModelOutput]]:
        """Parse raw data to model.

        :param raw_data: List of raw ModelOutput to parse.
        :return: Parsed data if succeeded.
        """
        try:
            files_data = [ModelOutput.parse_raw(op) for op in raw_data]
        except ValidationError as e:
            logger.error("parsing error %s", str(e))
            return None
        return files_data


class Page(BaseModel):
    """Class to store model output page."""

    page_num: int
    size: Size
    objs: List[GeometryObject]

    @staticmethod
    def merge(pages: List[Page]) -> Optional[Page]:
        """Merge pages into one by uniting its Geometry Objects.

        :param pages: Pages to merge.
        :return: Merged pages if succeeded.
        """
        objs = [obj for page in pages for obj in page.objs]
        united_objs = GeometryObject.unite_geometry_objects(objs)
        _page = pages[0] if pages else None
        if _page is None:
            logger.error("first page is None")
            return None
        page_num = _page.page_num
        size = _page.size
        return Page(page_num=page_num, size=size, objs=united_objs)

    @staticmethod
    def group_pages_by_page_num(pages: List[Page]) -> Dict[int, List[Page]]:
        """Group pages by its number."""
        grouped_pages = defaultdict(list)
        for page in pages:
            grouped_pages[page.page_num].append(page)
        return grouped_pages


class Size(BaseModel):
    width: float
    height: float


class GeometryObject(BaseModel):
    """Class to store model output page geometry object."""

    id: Union[int, str]
    type: Optional[str]
    segmentation: Optional[Dict[str, str]]
    bbox: Tuple[float, float, float, float]
    links: Optional[List[Dict[str, Any]]]
    category: str
    text: Optional[str]
    data: Optional[Dict[str, Any]]
    children: Optional[List[Union[int, str]]]
    tokens: Optional[List[int]]
    confidence: Optional[float]

    @staticmethod
    def unite_geometry_objects(
        objs: List[GeometryObject], id_start: int = 0
    ) -> List[GeometryObject]:
        """Unite Geometry Objects, resolving same id conflicts.

        :param objs: Objects to union.
        :param id_start: Id from which to start.
        :return: United objects.
        """
        grouped_objs = GeometryObject.group_objs_by_id(objs)
        unique_objs = []
        id_map = {}
        for id_, objs_ in enumerate(grouped_objs.values(), start=id_start):
            try:
                unique_objs.append(GeometryObject.merge(objs_, id_))
            except ValueError:
                continue
            id_map.update({objs_[-1].id: id_})
        GeometryObject.update_id(id_map, unique_objs)
        return unique_objs

    @staticmethod
    def update_id(
        id_map: Dict[Union[int, str], int],
        unique_objs: List[GeometryObject],
    ) -> None:
        """
        Change uuid to relevant integer ids for children and links fields
        """
        for unique_obj in unique_objs:
            if unique_obj.children is not None:
                unique_obj.children = [
                    id_map[child_id]
                    for child_id in unique_obj.children
                    if id_map[child_id] is not None
                ]
            if unique_obj.links is not None:
                for link in unique_obj.links:
                    link.update(
                        {"category": unique_obj.category, "to": unique_obj.id}
                    )

    @staticmethod
    def group_objs_by_id(
        objs: List[GeometryObject],
    ) -> Dict[Union[str, int], List[GeometryObject]]:
        """Group Geometry Objects by its id."""
        grouped_objs = defaultdict(list)
        for obj in objs:
            grouped_objs[obj.id].append(obj)
        return grouped_objs

    @staticmethod
    def merge(
        objs: List[GeometryObject], id_: Union[str, int] = 0
    ) -> GeometryObject:
        """Merge Geometry Objects into one.

        :param objs: Geometry Objects to merge.
        :param id_: Desired id of the object.
        :return: Merged Geometry Object
        """
        if not objs:
            logger.error("No GeometryObjects to merge")
            raise ValueError("No GeometryObjects to merge")
        type_ = objs[-1].type
        bbox = objs[-1].bbox
        segmentation = objs[-1].segmentation
        links = objs[-1].links
        category = objs[-1].category
        text = objs[-1].text
        data = {}
        children = objs[-1].children
        tokens = objs[-1].tokens
        confidence = objs[-1].confidence
        for obj in objs:
            data.update(obj.data) if obj.data else ...
        return GeometryObject(
            id=id_,
            type=type_,
            segmentation=segmentation,
            links=links,
            bbox=bbox,
            category=category,
            text=text,
            data=data if data else None,
            children=children,
            tokens=tokens,
            confidence=confidence,
        )


ModelOutput.update_forward_refs()
Page.update_forward_refs()


def get_annotation_uri(
    job_id: Union[str, int], file_id: Union[str, int]
) -> Optional[str]:
    """Create annotation URI for another file if Annotator URI is presented."""
    if not config.ANNOTATION_URI:
        logger.error("annotation url is None")
        return None
    base_uri = config.ANNOTATION_URI.rstrip("/")
    uri = f"{base_uri}/annotation/{job_id}/{file_id}".rstrip("/")
    return uri


def get_filename(path_: str) -> str:
    """Get filename from its path, excluding extension."""
    return path_.rstrip("/").rsplit("/", 1)[-1].split(".", 1)[0]


def get_file_data(client: Minio, bucket: str, filepath: str) -> bytes:
    """Extract data from file."""
    return client.get_object(bucket, filepath).data  # type: ignore


def list_object_names(client: Minio, bucket: str, path_: str) -> List[str]:
    """List object names with full path at the path recursively.

    :param client: Minio client.
    :param bucket: Bucket where to search.
    :param path_: Path where to search
    :return: List of object names.
    """
    objs = client.list_objects(bucket, prefix=path_, recursive=True)
    return [obj.object_name for obj in objs]


def get_pipeline_leaves_data(
    client: Minio, bucket: str, path_: str
) -> Optional[List[bytes]]:
    """Get pipeline leaves results from the storage.

    :param client: Minio client.
    :param bucket: Bucket where to search.
    :param path_: Path where to search.
    :return: List of leaves results if succeeded.
    """
    try:
        path_objects = list_object_names(client, bucket, path_)
        files_data = [
            get_file_data(client, bucket, path_) for path_ in path_objects
        ]
    except (minioerr.S3Error, urllib3.exceptions.MaxRetryError) as err:
        logger.error("error %s", str(err))
        return None
    return files_data


def merge_pipeline_leaves_data(
    client: Minio, bucket: str, path_: str
) -> Optional[ModelOutput]:
    """Get pipeline leaves data and merge it.

    :param client: Minio client.
    :param bucket: Bucket where to search.
    :param path_: Path where to search.
    :return: Merged data if succeeded.
    """
    files_data = get_pipeline_leaves_data(client, bucket, path_)
    if files_data is None:
        logger.error("merging minio data returns None")
        return None
    files_data_ = ModelOutput.parse_models(files_data)
    if files_data_ is None:
        logger.error("parsing merged data returns None")
        return None
    return ModelOutput.merge(files_data_)


def delete_objects(client: Minio, bucket: str, path_: str) -> bool:
    """Delete all objects recursively at the path.

    :param client: Minio client.
    :param bucket: Bucket to work with.
    :param path_: Path which objects to delete.
    :return: True if succeeded.
    """
    try:
        objects_list = list_object_names(client, bucket, path_)
        for obj in objects_list:
            client.remove_object(bucket, obj)
    except (minioerr.S3Error, urllib3.exceptions.MaxRetryError) as err:
        logger.error("error while removing, %s", str(err))
        return False
    return True


def postprocess_result(
    result: Dict[str, Any], headers: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Postprocess result by sending it to the Postprocessor microservice

    :param result: Result to postprocess.
    :param headers: Headers to postprocess.
    :return: Processed result if succeeded.
    """
    uri = config.POSTPROCESSING_URI
    if not uri:
        logger.error("postprocessing uri is None")
        return None
    try:
        resp = http_utils.make_request_with_retry(
            uri, result, method="POST", headers=headers
        )
        if resp is not None:
            return json.loads(resp.content)  # type: ignore
    except JSONDecodeError as err:
        logger.error("json error %s", str(err))

    return None


def manage_result_for_annotator(
    bucket: str,
    tenant: str,
    path_: str,
    job_id: int,
    file_bucket: str,
    filepath: str,
    file_id: str,
    pipeline_id: int,
    client: Minio,
    token: Optional[str],
) -> bool:
    """Manage result for by merging step results and sending it
    to Annotation Manager.

    :param bucket: Bucket with step results.
    :param tenant: Tenant name to use.
    :param job_id: Job id in which task is done.
    :param file_bucket: Bucket of the file.
    :param filepath: File path.
    :param path_: Path of the step results.
    :param file_id: File id (filename without extension).
    :param pipeline_id: id of executing pipeline.
    :param client: Client to connect to s3.
    :param token: service token.
    :return: True if succeeded.
    """
    uri = get_annotation_uri(job_id, file_id)
    if client is None or uri is None:
        logger.error("minio client or annotation uri are None")
        return False

    merged_data = merge_pipeline_leaves_data(client, bucket, path_)
    if merged_data is None:
        logger.error("merged data for postprocessing is None")
        return False

    data_for_postprocessor = {
        "file": filepath,
        "bucket": file_bucket,
        "input": merged_data.dict(exclude_none=True),
    }
    headers = {"X-Current-Tenant": tenant, "Authorization": f"Bearer {token}"}
    postprocessed_data = postprocess_result(data_for_postprocessor, headers=headers)
    if postprocessed_data is None:
        logger.info("result for postprocessing data is None")
        return False

    data_annotation = {
        "pipeline": pipeline_id,
        "pages": postprocessed_data["input"]["pages"],
    }
    resp = http_utils.make_request_with_retry(
        uri, data_annotation, method="POST", headers=headers
    )
    if resp is not None and resp.content:
        logger.info("successful response from annotation")
        logger.debug("response from annotation %s", resp.content)
        if not config.DEBUG_MERGE:
            logger.info("going to remove objects after merging")
            delete_objects(client, bucket, path_)
        return True

    logger.error("response from annotation is None")
    return False
