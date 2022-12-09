import abc
import copy
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from zipfile import ZipFile

import requests
from botocore.exceptions import ClientError

from src.config import minio_client, minio_resource, settings
from src.logger import get_logger
from src.models.coco import Annotation, Category, CocoDataset, Image
from src.utils.common_utils import add_to_zip_and_local_remove, get_headers
from src.utils.json_utils import export_save_to_json, load_from_json
from src.utils.render_pdf_page import pdf_page_to_jpg
from src.utils.s3_utils import convert_bucket_name_if_s3prefix

LOGGER = get_logger(__file__)


class DatasetFetch:
    def __init__(self, job_id: int, current_tenant: str, uuid: str):
        self.job_id = job_id
        self.tenant = current_tenant
        self.bucket_name = convert_bucket_name_if_s3prefix(self.tenant)
        self.uuid = uuid

    def load_input(self, file_id: int) -> str:
        """Load input json from Minio
        Args:
            file_id: id of the annotation
        Returns:
            Return path to loaded json
        """
        key = f"annotation/{self.job_id}/{file_id}"
        minio_client.download_file(self.bucket_name, key, key)
        return key

    def download_image(
        self,
        file_path: str,
        zip_file: ZipFile,
        pages: Optional[Dict[str, str]] = None,
        validated_pages: Optional[List[int]] = None,
    ) -> str:
        """Download file from Minio
        Returns:
            local path to image
        """
        image_folder = f"{Path(file_path).parent.parent}/"
        if not os.path.exists(image_folder):
            os.makedirs(image_folder, exist_ok=True)
        image_local_path = (
            f"{image_folder}/{self.job_id}_{Path(file_path).name}"
        )
        minio_resource.meta.client.download_file(
            self.bucket_name, file_path, image_local_path
        )
        LOGGER.info("file %s was downloaded", Path(file_path).name)
        if Path(file_path).suffix == ".pdf" and validated_pages:
            pdf_page_to_jpg(
                Path(image_local_path),
                Path(image_local_path).parent,
                zip_file,
                self.job_id,
                validated_pages=validated_pages,
            )
        elif Path(file_path).suffix == ".pdf" and not validated_pages:
            pdf_page_to_jpg(
                Path(image_local_path),
                Path(image_local_path).parent,
                zip_file,
                self.job_id,
            )
        elif Path(file_path).suffix != ".pdf" and validated_pages:
            page = next(iter(pages))  # type: ignore
            if int(page) in validated_pages:
                add_to_zip_and_local_remove(image_local_path, zip_file)
        else:
            LOGGER.info(
                "image %s was written to archive %s",
                Path(file_path).name,
                zip_file.filename,
            )
            add_to_zip_and_local_remove(image_local_path, zip_file)
        return image_local_path

    def download_annotation(
        self,
        work_dir: Path,
        pages: Dict[str, str],
        zip_file: ZipFile,
        validated_pages: Optional[List[int]] = None,
    ) -> None:
        """
        Download annotation json from minio
        """
        _, job_path, file_path = str(work_dir).split("/")
        local_path = f"{job_path}/{file_path}"
        if not os.path.exists(local_path):
            os.makedirs(local_path, exist_ok=True)
        for page_num, page_name in pages.items():
            if validated_pages and int(page_num) not in validated_pages:
                continue
            minio_client.download_file(
                self.bucket_name,
                f"{work_dir}/{page_name}.json",
                f"{local_path}/{page_name}.json",
            )
            add_to_zip_and_local_remove(
                f"{local_path}/{page_name}.json", zip_file
            )

    def get_annotation_body(
        self,
        work_dir: Path,
        pages: Dict[str, str],
        validated_pages: Optional[List[int]] = None,
    ) -> List[str]:
        """
        Get annotation of pages
        """
        annotation_content_lst = []
        for page_num, page_name in pages.items():
            if validated_pages and int(page_num) not in validated_pages:
                continue
            annotation_page_content = json.loads(
                minio_client.get_object(
                    Bucket=self.bucket_name, Key=f"{work_dir}/{page_name}.json"
                )["Body"].read()
            )
            annotation_content_lst.append(annotation_page_content)
        return annotation_content_lst

    def fetch(
        self,
        manifest: str,
        zip_file: ZipFile,
        download: bool = False,
        validated_only: bool = False,
    ) -> Any:
        """Download manifest json and json annotation for each page
        Returns:
            Return tuple of the pages list, path to an output directory list,
            path to pdf document list, path to output directory/ dataset name
        """
        work_dir = Path(manifest).parent
        manifest_content = json.loads(
            minio_client.get_object(Bucket=self.bucket_name, Key=manifest)[
                "Body"
            ]
            .read()
            .decode("utf-8")
        )
        pages = manifest_content["pages"]
        file = manifest_content["file"]
        if validated_only:
            if any(
                validate_page
                for validate_page in manifest_content["validated"]
                if str(validate_page) not in manifest_content["pages"].keys()
            ):
                LOGGER.error("Validated page doesn't exist")
                raise KeyError("Validated page doesn't exist")
            validated_pages = manifest_content["validated"]
            if download:
                self.download_annotation(
                    work_dir, pages, zip_file, validated_pages=validated_pages
                )
                self.download_image(
                    file,
                    zip_file,
                    pages=pages,
                    validated_pages=validated_pages,
                )
            else:
                annotation_lst = self.get_annotation_body(
                    work_dir, pages, validated_pages=validated_pages
                )
                image_content = self.download_image(
                    file,
                    zip_file,
                    pages=pages,
                    validated_pages=validated_pages,
                )
                return annotation_lst, image_content
        else:
            if download:
                self.download_annotation(work_dir, pages, zip_file)
                self.download_image(file, zip_file)
            else:
                annotation_lst = self.get_annotation_body(work_dir, pages)
                image_content = self.download_image(file, zip_file)
                return annotation_lst, image_content

    def get_categories(self, token: str) -> List[str]:
        """Get categories from minio"""
        response = requests.post(
            f"{settings.category_service_url}search",
            headers=get_headers(token, self.tenant),
            json={"pagination": {"page_num": 1, "page_size": 100}},
        )
        response.raise_for_status()
        response_data = response.json()["data"]
        categories = [category_name["name"] for category_name in response_data]
        return categories

    def is_job_exist(self) -> Union[List[Dict[str, str]], ClientError]:
        """Existence check of the job"""
        try:
            file_id = minio_client.list_objects(
                Bucket=self.bucket_name,
                Prefix=f"annotation/{self.job_id}/",
                Delimiter="/",
            )["CommonPrefixes"]
            return file_id
        except KeyError as ex:
            LOGGER.error("Job doesn't exist")
            raise ClientError(
                operation_name="NuSuchPath.NotJob",
                error_response={
                    "Error": {"Code": "NotJob", "Message": "Job doesn't exist"}
                },
            )


class ExportConvertBase:
    def __init__(
        self,
        job_id: int,
        tenant: str,
        token: str,
        uuid: str,
        export_format: str,
        validated_only: bool = False,
    ):
        self.job_id = job_id
        self.tenant = tenant
        self.bucket_name = convert_bucket_name_if_s3prefix(self.tenant)
        self.token = token
        self.uuid = uuid
        self.zip_name = f"{self.uuid}_{export_format}.zip"
        self.validated_only = validated_only

    @property
    def zip_file(self) -> ZipFile:
        return ZipFile(self.zip_name, "a", compression=zipfile.ZIP_DEFLATED)

    @abc.abstractmethod
    def convert_to_coco(
        self,
        annotation_content: List[Dict[str, Any]],
        image_path: str,
        annotation_num: int,
        categories: List[str],
        category_names: Dict[str, int],
    ) -> Union[Any, ZipFile]:
        """Convert format to Coco
        Returns:
            Zipfile with coco annotation and images
        """
        pass

    @abc.abstractmethod
    def convert(self) -> ZipFile:
        """Download data, convert it to input format and
        upload results to minio

        Returns:
            Zipfile with images and coco format annotation
        """
        pass


class ConvertToCoco(ExportConvertBase):
    def convert(self) -> ZipFile:
        loader = DatasetFetch(self.job_id, self.tenant, self.uuid)
        file_id = loader.is_job_exist()
        coco_annotation = CocoDataset(annotations=[], images=[], categories=[])
        annotation_num = 1
        categories = loader.get_categories(self.token)
        category_names = {
            category.lower(): number
            for number, category in enumerate(categories)
        }
        for page in file_id:
            files = minio_client.list_objects(
                Bucket=self.bucket_name, Prefix=page["Prefix"]
            )["Contents"]
            manifest_path = [
                file for file in files if Path(file["Key"]).stem == "manifest"
            ][0]["Key"]
            annotation_page_content, image_local_path = loader.fetch(
                manifest_path,
                self.zip_file,
                validated_only=self.validated_only,
            )
            annotation, annotation_num = self.convert_to_coco(
                annotation_page_content,
                image_local_path,
                annotation_num,
                categories,
                category_names,
            )
            coco_annotation.annotations.extend(annotation.annotations)
            coco_annotation.images.extend(annotation.images)
            coco_annotation.categories.extend(annotation.categories)
        coco_annotation.categories = sorted(
            list(
                {
                    v.dict()["name"]: v.dict() for v in coco_annotation.categories  # type: ignore
                }.values()
            ),
            key=lambda x: x["id"],  # type: ignore
        )
        export_save_to_json("coco", coco_annotation.dict())
        LOGGER.info(
            "Converting of the job %s to coco has been finished", self.job_id
        )
        self.zip_file.close()
        return self.zip_file

    def convert_to_coco(
        self,
        pages: List[Dict[str, Any]],
        image_path: str,
        annotation_num: int,
        categories: List[str],
        category_names: Dict[str, int],
    ) -> Tuple[CocoDataset, int]:
        """Convert format to Coco
        Returns:
            Zipfile with coco annotation and images
        """
        annotation = CocoDataset(annotations=[], images=[], categories=[])
        for page in sorted(pages, key=lambda x: x["page_num"]):  # type: ignore
            if not page:
                raise ValueError("Annotation file is empty")
            image_id = (
                page["page_num"]
                if Path(image_path).suffix == ".pdf"
                else int(Path(image_path).stem.split("_")[1])
            )
            for element in page["objs"]:
                if element["category"] not in category_names:
                    response = requests.post(
                        settings.category_service_url,
                        headers=get_headers(self.token, self.tenant),
                        json={
                            "name": element["category"],
                            "parent": None,
                            "is_link": False,
                        },
                    )
                    response.raise_for_status()
                    categories.append(element["category"])
                category_id = category_names[element["category"]]
                annotation_obj = Annotation(
                    id=annotation_num,
                    image_id=image_id,
                    bbox=[
                        float(element["bbox"][0]),
                        float(element["bbox"][1]),
                        round(element["bbox"][2] - element["bbox"][0], 2),
                        round(element["bbox"][3] - element["bbox"][1], 2),
                    ],
                    category_id=category_id,
                    area=round(element["bbox"][3] * element["bbox"][2], 2),
                    isbbox=bool(element["bbox"]),
                )
                if element["category"] in categories:
                    category = Category(
                        id=category_id if isinstance(category_id, int) else 0,
                        name=element["category"],
                        supercategory="none",
                    )
                    annotation.categories.append(category)
                    categories.remove(element["category"])
                annotation.annotations.append(annotation_obj)
                annotation_num += 1
            annotation.images.append(
                Image(
                    id=image_id,
                    file_name=f"{self.job_id}_{image_id}.{settings.coco_image_format}",
                    width=page["size"]["width"],
                    height=page["size"]["height"],
                )
            )
        return annotation, annotation_num


class ExportBadgerdoc(ExportConvertBase):
    def convert(self) -> ZipFile:
        """
        Download images and annotation for them.
        Write the result to zip file
        """
        loader = DatasetFetch(self.job_id, self.tenant, self.uuid)
        file_id = loader.is_job_exist()
        for page in file_id:
            files = minio_client.list_objects(
                Bucket=self.bucket_name, Prefix=page["Prefix"]
            )["Contents"]
            manifest_path = [
                file for file in files if Path(file["Key"]).stem == "manifest"
            ][0]["Key"]
            base_path, job, file, file_name = manifest_path.split("/")
            annotation_local_path = f"{job}/{file}/{file_name}"
            if not os.path.exists(Path(annotation_local_path).parent):
                os.makedirs(Path(annotation_local_path).parent, exist_ok=True)
            minio_client.download_file(
                self.bucket_name, manifest_path, annotation_local_path
            )
            LOGGER.info(
                "manifest.json was downloaded for the job %s", self.job_id
            )
            add_to_zip_and_local_remove(annotation_local_path, self.zip_file)
            loader.fetch(
                manifest_path,
                self.zip_file,
                download=True,
                validated_only=self.validated_only,
            )
        return self.zip_file
