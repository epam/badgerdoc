import random
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import requests
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from tenant_dependency import TenantData

from src.config import DEFAULT_PAGE_BORDER_OFFSET, settings
from src.label_studio_to_badgerdoc.badgerdoc_format.annotation_converter import (
    AnnotationConverter,
)
from src.label_studio_to_badgerdoc.badgerdoc_format.badgerdoc_format import (
    BadgerdocFormat,
)
from src.label_studio_to_badgerdoc.badgerdoc_format.pdf_renderer import (
    PDFRenderer,
)
from src.label_studio_to_badgerdoc.badgerdoc_format.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)
from src.label_studio_to_badgerdoc.models import BadgerdocToken
from src.label_studio_to_badgerdoc.models.label_studio_models import (
    LabelStudioModel,
    S3Path,
    ValidationType,
)
from src.logger import get_logger

LOGGER = get_logger(__file__)
LOGGER.setLevel("DEBUG")


class LabelStudioToBDConvertUseCase:

    converted_annotations_filename = "annotations.json"
    converted_tokens_filename = "1.json"
    output_pdf_filename = "badgerdoc_render.pdf"
    badgerdoc_tokens_filename = "badgerdoc_tokens.json"
    badgerdoc_annotations_filename = "badgerdoc_annotations.json"

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

    def execute(self) -> None:
        label_studio_format = self.download_label_studio_from_s3(
            self.s3_input_annotation
        )
        LOGGER.debug("label studio format: %s", label_studio_format)
        self.badgerdoc_format.convert_from_labelstudio(label_studio_format)
        LOGGER.debug("Tokens and annotations are converted")
        file_id_in_assets = self.upload_output_pdf_to_s3()
        importjob_id_created = (
            self.import_annotations_to_annotation_microservice(
                file_id_in_assets=file_id_in_assets,
                owner=self.token_data.user_id,
                validation_type=self.validation_type,
                deadline=self.deadline,
                extensive_coverage=self.extensive_coverage,
                annotators=self.annotators,
                validators=self.validators,
            )
        )
        self.upload_badgerdoc_annotations_and_tokens_to_s3(
            importjob_id_created, file_id_in_assets
        )
        LOGGER.debug("Tokens and annotations uploaded")

    def download_label_studio_from_s3(
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
            f"files/{file_id_in_assets}/ocr/{self.converted_tokens_filename}"
        )

    def get_output_pdf_path(self, file_id_in_assets: int) -> str:
        return f"files/{file_id_in_assets}/{file_id_in_assets}.pdf"

    def get_output_annotations_path(
        self, importjob_id_created: int, file_id_in_assets: int
    ) -> str:
        return f"annotation/{importjob_id_created}/{file_id_in_assets}/{self.converted_annotations_filename}"

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
            pdf_path = tmp_dirname / Path(self.output_pdf_filename)
            self.badgerdoc_format.export_pdf(pdf_path)

            file_id_in_assets = self.make_upload_file_request_to_assets(
                pdf_path
            )
            return file_id_in_assets

    def upload_badgerdoc_annotations_and_tokens_to_s3(
        self, importjob_id_created: int, file_id_in_assets: int
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)

            s3_output_tokens_path = self.get_output_tokens_path(
                file_id_in_assets
            )

            badgerdoc_tokens_path = tmp_dirname / Path(
                self.badgerdoc_tokens_filename
            )
            self.badgerdoc_format.export_tokens(badgerdoc_tokens_path)
            self.s3_client.upload_file(
                str(badgerdoc_tokens_path),
                self.s3_output_bucket,
                s3_output_tokens_path,
            )

            badgerdoc_annotations_path = tmp_dirname / Path(
                self.badgerdoc_annotations_filename
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

    def request_jobs_to_create_annotation_job(
        self,
        file_id_in_assets: int,
        owner: str,
        validation_type: ValidationType,
        deadline: datetime,
        extensive_coverage: int,
        annotators: List[str],
        validators: List[str],
    ) -> int:
        categories = self.request_annotations_to_post_categories()
        post_annotation_job_url = f"{settings.job_service_url}create_job/"
        post_annotation_job_body = {
            "name": f"import_label_studio_job_{uuid4()}",
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

    def form_post_category_body(
        self, type_of_categories: str, category: str
    ) -> Dict[str, Any]:
        possible_categories_colors = (
            "#FF0000",  # red
            "#FFFF00",  # yellow
            "#008000",  # green
            "#0000FF",  # blue
            "#FF00FF",  # pyrple
            "#808080",  # grey
            "#800000",  # brown
        )

        result = {
            "name": category,
            "type": type_of_categories,
            "id": category,
            "metadata": {"color": random.choice(possible_categories_colors)},
        }
        return result

    def request_annotations_to_post_categories(self) -> List[str]:
        post_categories_url = f"{settings.annotation_service_url}categories/"
        LOGGER.debug(
            "Making requests to url: %s to post annotations",
            post_categories_url,
        )
        pages_objs = self.badgerdoc_format.badgerdoc_annotation.pages[0].objs
        categories_of_type_box = {
            pages_obj.category for pages_obj in pages_objs
        }
        categories_of_type_link = self.get_categories_of_links(pages_objs)
        all_categories = {
            "box": categories_of_type_box,
            "link": categories_of_type_link,
        }

        for (
            type_of_categories,
            set_of_categories_names,
        ) in all_categories.items():
            for category in set_of_categories_names:
                post_categories_body = self.form_post_category_body(
                    type_of_categories, category
                )
                LOGGER.debug(
                    "Making request to post categories with this request body: %s",
                    post_categories_body,
                )

                try:
                    request_to_post_categories = requests.post(
                        url=post_categories_url,
                        headers=self.request_headers,
                        json=post_categories_body,
                    )
                    request_to_post_categories.raise_for_status()
                except requests.exceptions.RequestException as e:
                    if request_to_post_categories.status_code == 400 and request_to_post_categories.json() == {
                        "detail": "Field constraint error. Category id must be unique."
                    }:
                        LOGGER.warning(
                            "Category %s already exists in annotation. Skipping this request",
                            category,
                        )
                        continue

                    LOGGER.exception(
                        "Failed request to 'annotation' to post categories for converted annotations"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Failed request to 'annotation' to post categories for converted annotations",
                    ) from e

                LOGGER.debug(
                    "Got this response from annotation service: %s",
                    request_to_post_categories.json(),
                )

        return [*categories_of_type_box, *categories_of_type_link]

    def request_annotation_to_post_annotations(
        self, importjob_id_created: int, file_id_in_assets: int
    ) -> None:
        annotations_post_url = f"{settings.annotation_service_url}annotation/{importjob_id_created}/{file_id_in_assets}"

        pages = self.badgerdoc_format.badgerdoc_annotation.pages
        annotations_post_body = {
            "base_revision": None,
            "pipeline": 0,
            "pages": [page.dict() for page in pages],
            "validated": [],
            "failed_validation_pages": [],
            "similar_revisions": [],  # TODO: 'simial_revisions' will be replaced with 'links' with unknown format
            "categories": [],  # TODO: how to parse 'categories' will be determined in future
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
    ) -> int:
        annotation_job_id_created = self.request_jobs_to_create_annotation_job(
            file_id_in_assets,
            owner,
            validation_type,
            deadline,
            extensive_coverage,
            annotators,
            validators,
        )
        self.request_annotation_to_post_annotations(
            annotation_job_id_created, file_id_in_assets
        )

        return annotation_job_id_created
