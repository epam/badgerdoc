import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Union
from uuid import uuid4

import requests
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from tenant_dependency import TenantData

from src.badgerdoc_format.badgerdoc_format import BadgerdocFormat
from src.badgerdoc_format.bd_annotation_model_practic import DocumentLink
from src.badgerdoc_format.bd_tokens_model import BadgerdocToken
from src.badgerdoc_format.pdf_renderer import PDFRenderer
from src.config import DEFAULT_PAGE_BORDER_OFFSET, settings
from src.labelstudio_format.annotation_converter import AnnotationConverter
from src.labelstudio_format.ls_models import LabelStudioModel, ValidationType
from src.labelstudio_format.converter import Converter
from src.logger import get_logger
from src.models.common import S3Path
from src.plain_text_format.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)

LOGGER = get_logger(__file__)
LOGGER.setLevel("DEBUG")


class LabelstudioToBadgerdocConverter:

    CONVERTED_ANNOTATIONS_FILENAME = "annotations.json"
    CONVERTED_TOKENS_FILENAME = "1.json"
    OUTPUT_PDF_FILENAME = "badgerdoc_render.pdf"
    BADGERDOC_TOKENS_FILENAME = "badgerdoc_tokens.json"
    BADGERDOC_ANNOTATIONS_FILENAME = "badgerdoc_annotations.json"

    def __init__(
        self,
        s3_client: BaseClient,
        current_tenant: str,
        token_data: TenantData,
        s3_input_annotation: S3Path,
        s3_output_bucket: str,
        validation_type: ValidationType,
        deadline: datetime,
        extensive_coverage: int,
        annotators: List[str],
        validators: List[str],
    ) -> None:
        page_border_offset = DEFAULT_PAGE_BORDER_OFFSET
        self.plain_text_converter = TextToBadgerdocTokensConverter(
            page_border_offset=page_border_offset
        )
        self.pdf_renderer = PDFRenderer(page_border_offset=page_border_offset)
        self.annotation_converter = AnnotationConverter()
        self.badgerdoc_format = BadgerdocFormat()
        self.s3_client = s3_client

        self.current_tenant = current_tenant
        self.token_data = token_data
        self.request_headers = {
            "X-Current-Tenant": self.current_tenant,
            "Authorization": f"Bearer {self.token_data.token}",
        }
        self.s3_input_annotation = s3_input_annotation
        self.s3_output_bucket = s3_output_bucket
        self.validation_type = validation_type
        self.deadline = deadline
        self.extensive_coverage = extensive_coverage
        self.annotators = annotators
        self.validators = validators

    def parse_document_labels_from_ls_format(
        self, ls_format: LabelStudioModel
    ) -> Set[str]:
        document_labels = ls_format.__root__[0].meta.labels
        return {label["name"] for label in document_labels}

    @staticmethod
    def parse_categories_to_taxonomy_mapping_from_ls_format(
        ls_format: LabelStudioModel,
    ) -> Dict[str, Any]:
        categories_to_taxonomy_mapping = ls_format.__root__[
            0
        ].meta.categories_to_taxonomy_mapping
        return categories_to_taxonomy_mapping

    @staticmethod
    def parse_document_links_from_ls_format(
        ls_format: LabelStudioModel,
    ) -> List[DocumentLink]:
        return [
            DocumentLink(
                to=relation.to, category=relation.category, type=relation.type
            )
            for relation in ls_format.__root__[0].meta.relations
        ]

    def execute(self) -> None:
        ls_format = self.download(self.s3_input_annotation)
        LOGGER.debug("label studio format: %s", ls_format)
        document_labels = self.parse_document_labels_from_ls_format(ls_format)
        categories_to_taxonomy_mapping = (
            self.parse_categories_to_taxonomy_mapping_from_ls_format(ls_format)
        )
        document_links = self.parse_document_links_from_ls_format(ls_format)

        LOGGER.debug("document_labels parsed: %s", document_labels)

        ls_converter = Converter()
        ls_converter.to_badgerdoc(ls_format)
        self.badgerdoc_format.tokens_page = ls_converter.tokens_page
        self.badgerdoc_format.badgerdoc_annotation = ls_converter.badgerdoc_annotation

        LOGGER.debug("Tokens and annotations are converted")
        file_id_in_assets = self.upload_output_pdf_to_s3()
        annotation_job_id_created = (
            self.import_annotations_to_annotation_microservice(
                file_id_in_assets=file_id_in_assets,
                owner=self.token_data.user_id,
                validation_type=self.validation_type,
                deadline=self.deadline,
                extensive_coverage=self.extensive_coverage,
                annotators=self.annotators,
                validators=self.validators,
                document_labels=document_labels,
                categories_to_taxonomy_mapping=categories_to_taxonomy_mapping,
                document_links=document_links,
            )
        )
        self.upload(annotation_job_id_created, file_id_in_assets)
        LOGGER.debug("Tokens and annotations uploaded")

    def download(
        self,
        s3_input_annotation: S3Path,
    ) -> LabelStudioModel:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            input_file = (
                Path(tmp_dirname) / Path(s3_input_annotation.path).name
            )

            try:
                self.s3_client.download_file(
                    s3_input_annotation.bucket,
                    s3_input_annotation.path,
                    str(input_file),
                )
            except ClientError as e:
                LOGGER.exception(
                    "Cannot download file from S3: bucket %s path %s",
                    s3_input_annotation.bucket,
                    s3_input_annotation.path,
                )
                raise HTTPException(
                    status_code=404,
                    detail="Error during file fetching: file not found",
                ) from e

            return LabelStudioModel.parse_file(input_file)

    def get_output_tokens_path(self, file_id_in_assets: int) -> str:
        return (
            f"files/{file_id_in_assets}/ocr/{self.CONVERTED_TOKENS_FILENAME}"
        )

    def get_output_pdf_path(self, file_id_in_assets: int) -> str:
        return f"files/{file_id_in_assets}/{file_id_in_assets}.pdf"

    def get_output_annotations_path(
        self, importjob_id_created: int, file_id_in_assets: int
    ) -> str:
        return f"annotation/{importjob_id_created}/{file_id_in_assets}/{self.CONVERTED_ANNOTATIONS_FILENAME}"

    def make_upload_file_request_to_assets(self, pdf_path: Path) -> int:
        upload_file_to_assets_url = f"{settings.assets_service_url}"
        files = [
            (
                "files",
                (pdf_path.name, open(pdf_path, "rb"), "application/pdf"),
            ),
        ]
        try:
            request_to_post_assets = requests.post(
                url=upload_file_to_assets_url,
                headers=self.request_headers,
                files=files,
            )
            request_to_post_assets.raise_for_status()
        except requests.exceptions.RequestException as e:
            LOGGER.exception(
                "Failed request to 'assets' to post converted pdf-file"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed request to 'assets' to post converted pdf-file",
            ) from e
        return request_to_post_assets.json()[0]["id"]

    def upload_output_pdf_to_s3(self) -> int:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            pdf_path = tmp_dirname / Path(self.OUTPUT_PDF_FILENAME)
            self.badgerdoc_format.export_pdf(pdf_path)

            file_id_in_assets = self.make_upload_file_request_to_assets(
                pdf_path
            )
            return file_id_in_assets

    def upload(
        self, importjob_id_created: int, file_id_in_assets: int
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)

            s3_output_tokens_path = self.get_output_tokens_path(
                file_id_in_assets
            )

            badgerdoc_tokens_path = tmp_dirname / Path(
                self.BADGERDOC_TOKENS_FILENAME
            )
            self.badgerdoc_format.export_tokens(badgerdoc_tokens_path)
            self.s3_client.upload_file(
                str(badgerdoc_tokens_path),
                self.s3_output_bucket,
                s3_output_tokens_path,
            )

            badgerdoc_annotations_path = tmp_dirname / Path(
                self.BADGERDOC_ANNOTATIONS_FILENAME
            )
            self.badgerdoc_format.export_annotations(
                badgerdoc_annotations_path
            )
            s3_output_annotations_path = self.get_output_annotations_path(
                importjob_id_created, file_id_in_assets
            )
            self.s3_client.upload_file(
                str(badgerdoc_annotations_path),
                self.s3_output_bucket,
                s3_output_annotations_path,
            )

    @staticmethod
    def enrich_categories_with_taxonomies(
        categories: List[str],
        categories_to_taxonomy_mapping: Dict[str, Any],
    ) -> List[Union[str, Dict[str, Any]]]:
        for (
            linked_category,
            taxonomy_obj,
        ) in categories_to_taxonomy_mapping.items():
            formatted_obj = {
                "category_id": linked_category,
                "taxonomy_id": taxonomy_obj["taxonomy_id"],
                "taxonomy_version": taxonomy_obj["version"],
            }
            categories.append(formatted_obj)
        return categories

    def request_jobs_to_create_annotation_job(
        self,
        file_id_in_assets: int,
        owner: str,
        validation_type: ValidationType,
        deadline: datetime,
        extensive_coverage: int,
        annotators: List[str],
        validators: List[str],
        document_labels: Set[str],
        categories_to_taxonomy_mapping: Dict[str, Any],
        document_links: List[DocumentLink],
    ) -> int:
        categories = self.get_box_and_link_categories() + list(document_labels)
        LOGGER.debug("categories: %s", categories)
        categories = self.enrich_categories_with_taxonomies(
            categories, categories_to_taxonomy_mapping
        )
        LOGGER.debug("categories with taxonomy_objs: %s", categories)

        categories_of_links = [link.category for link in document_links]
        LOGGER.debug("categories of document links: %s", categories_of_links)
        categories.extend(categories_of_links)

        post_annotation_job_url = f"{settings.job_service_url}create_job/"
        post_annotation_job_body = {
            "name": f"import_labelstudio_job_{uuid4()}",
            "type": "AnnotationJob",
            "files": [file_id_in_assets],
            "datasets": [],
            "is_draft": False,
            "validation_type": validation_type,
            "annotators": annotators,
            "owners": [owner],
            "categories": categories,
            "validators": validators,
        }
        if deadline:
            post_annotation_job_body.update(
                {"deadline": jsonable_encoder(deadline)}
            )
        if extensive_coverage is not None:
            post_annotation_job_body.update(
                {"extensive_coverage": extensive_coverage}
            )
        LOGGER.debug(
            "Making a request to create an Annotation Job in 'jobs' to url: %s with request body: %s",
            post_annotation_job_url,
            post_annotation_job_body,
        )

        try:
            request_to_post_annotation_job = requests.post(
                url=post_annotation_job_url,
                headers=self.request_headers,
                json=post_annotation_job_body,
            )
            request_to_post_annotation_job.raise_for_status()
        except requests.exceptions.RequestException as e:
            LOGGER.exception("Failed request to 'jobs' to post AnnotationJob")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed request to 'jobs' to post AnnotationJob",
            ) from e

        LOGGER.debug(
            "Got this response from jobs service: %s",
            request_to_post_annotation_job.json(),
        )
        return request_to_post_annotation_job.json()["id"]

    def get_categories_of_links(
        self, pages_objs: List[BadgerdocToken]
    ) -> List[str]:
        result = []
        for pages_obj in pages_objs:
            for link in pages_obj.links:
                result.append(link.category_id)

        return result

    def get_box_and_link_categories(self) -> List[str]:
        pages_objs = self.badgerdoc_format.badgerdoc_annotation.objs
        categories_of_type_box = {
            pages_obj.category for pages_obj in pages_objs
        }
        categories_of_type_link = self.get_categories_of_links(pages_objs)
        return [*categories_of_type_box, *categories_of_type_link]

    def request_annotation_to_post_annotations(
        self,
        annotation_job_id_created: int,
        file_id_in_assets: int,
        document_labels: Set[str],
        document_links: List[DocumentLink],
    ) -> None:
        annotations_post_url = f"{settings.annotation_service_url}annotation/{annotation_job_id_created}/{file_id_in_assets}"

        page = self.badgerdoc_format.badgerdoc_annotation
        annotations_post_body = {
            "base_revision": None,
            "pipeline": 0,
            "pages": [page.dict()],
            "validated": [],
            "failed_validation_pages": [],
            "similar_revisions": [],  # TODO: 'simial_revisions' will be replaced with 'links' with unknown format
            "categories": list(document_labels),
            "links_json": [
                document_link.dict() for document_link in document_links
            ],
        }
        LOGGER.debug(
            "Making request to annotation to post annotations to url: %s with request body: %s",
            annotations_post_url,
            annotations_post_body,
        )

        try:
            request_to_post_annotations = requests.post(
                url=annotations_post_url,
                headers=self.request_headers,
                json=annotations_post_body,
            )
            request_to_post_annotations.raise_for_status()
        except requests.exceptions.RequestException as e:
            LOGGER.exception(
                "Failed request to 'annotation' to post converted annotations"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed request to 'annotation' to post converted annotations",
            ) from e

        LOGGER.debug(
            "Got this response from annotation service: %s",
            request_to_post_annotations.json(),
        )

    def import_annotations_to_annotation_microservice(
        self,
        file_id_in_assets: int,
        owner: str,
        validation_type: ValidationType,
        deadline: datetime,
        extensive_coverage: int,
        annotators: List[str],
        validators: List[str],
        document_labels: Set[str],
        categories_to_taxonomy_mapping: Dict[str, Any],
        document_links: List[DocumentLink],
    ) -> int:
        annotation_job_id_created = self.request_jobs_to_create_annotation_job(
            file_id_in_assets,
            owner,
            validation_type,
            deadline,
            extensive_coverage,
            annotators,
            validators,
            document_labels,
            categories_to_taxonomy_mapping,
            document_links,
        )
        self.request_annotation_to_post_annotations(
            annotation_job_id_created,
            file_id_in_assets,
            document_labels,
            document_links,
        )

        return annotation_job_id_created
