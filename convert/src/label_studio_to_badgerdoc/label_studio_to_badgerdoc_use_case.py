import tempfile
from pathlib import Path
from uuid import uuid4

import requests
from botocore.exceptions import ClientError
from fastapi import HTTPException
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
from src.label_studio_to_badgerdoc.models.label_studio_models import (
    LabelStudioModel,
    S3Path,
)
from src.logger import get_logger

LOGGER = get_logger(__file__)


class LabelStudioToBDConvertUseCase:
    def __init__(
        self,
        s3_client,
        current_tenant: str,
        token_data: TenantData,
        s3_input_annotation: S3Path,
        s3_output_bucket: str,
        s3_output_file_id: int,
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
        self.s3_output_file_id = s3_output_file_id

    def execute(self) -> None:
        label_studio_format = self.download_label_studio_from_s3(
            self.s3_input_annotation
        )
        LOGGER.debug(f"label studio format {label_studio_format=}")
        self.badgerdoc_format.convert_from_labelstudio(label_studio_format)
        LOGGER.debug("Tokens and annotations are converted")
        importjob_id_created = (
            self.import_annotations_to_annotation_microservice()
        )
        self.upload_badgerdoc_format_to_s3(importjob_id_created)
        LOGGER.debug("Tokens and annotations uploaded")

    def download_label_studio_from_s3(
        self,
        s3_input_annotation: S3Path,
    ) -> LabelStudioModel:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)
            input_file = tmp_dirname / Path(s3_input_annotation.path).name

            try:

                self.s3_client.download_file(
                    s3_input_annotation.bucket,
                    s3_input_annotation.path,
                    str(input_file),
                )

            except ClientError as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"Request to download label studio file failed - {e}",
                )

            result = LabelStudioModel.parse_file(input_file)
            return result

    def get_output_tokens_path(self):
        return f"files/{self.s3_output_file_id}/ocr/tokens.json"

    def get_output_pdf_path(self):
        return f"files/{self.s3_output_file_id}/{self.s3_output_file_id}.pdf"

    def get_output_annotations_path(self, importjob_id_created: int):
        return f"annotation/{importjob_id_created}/{self.s3_output_file_id}/annotation.json"

    def upload_badgerdoc_format_to_s3(self, importjob_id_created: int) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)

            s3_output_tokens_path = self.get_output_tokens_path()

            badgerdoc_tokens_path = tmp_dirname / Path("badgerdoc_tokens.json")
            self.badgerdoc_format.export_tokens(badgerdoc_tokens_path)
            self.s3_client.upload_file(
                str(badgerdoc_tokens_path),
                self.s3_output_bucket,
                s3_output_tokens_path,
            )

            pdf_path = tmp_dirname / Path("badgerdoc_render.pdf")
            self.badgerdoc_format.export_pdf(pdf_path)

            s3_output_pdf_path = self.get_output_pdf_path()
            self.s3_client.upload_file(
                str(pdf_path), self.s3_output_bucket, s3_output_pdf_path
            )

            badgerdoc_annotations_path = tmp_dirname / Path(
                "badgerdoc_annotations.json"
            )
            self.badgerdoc_format.export_annotations(
                badgerdoc_annotations_path
            )
            s3_output_annotations_path = self.get_output_annotations_path(
                importjob_id_created
            )
            self.s3_client.upload_file(
                str(badgerdoc_annotations_path),
                self.s3_output_bucket,
                s3_output_annotations_path,
            )

    def request_jobs_to_create_importjob(self):
        post_importjob_url = f"{settings.job_service_url}create_job/"
        post_importjob_body = {
            "name": f"import_job_{uuid4()}",
            "type": "ImportJob",
            "import_source": self.s3_input_annotation.path,
            "import_format": "Label Studio",
            "owners": [
                self.token_data.user_id,
            ],
            "files": [],
            "categories": [],
        }
        LOGGER.debug(f"{post_importjob_url=}")
        LOGGER.debug(f"{post_importjob_body=}")

        try:
            request_to_post_importjob = requests.post(
                url=post_importjob_url,
                headers=self.request_headers,
                json=post_importjob_body
            )
            request_to_post_importjob.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed request to 'jobs' - {e}"
            ) from e

        else:
            LOGGER.debug(f"{request_to_post_importjob.json()=}")
            return request_to_post_importjob.json()["id"]

    def request_annotations_to_post_categories(self):
        post_categories_url = f"{settings.annotation_service_url}categories/"
        LOGGER.debug(f"{post_categories_url=}")

        pages_objs = self.badgerdoc_format.badgerdoc_annotation.pages[0].objs
        categories = {pages_obj.category for pages_obj in pages_objs}

        for category in categories:
            post_categories_body = {
                "name": category,
                "type": "box",
                "id": category,
            }
            LOGGER.debug(f"{post_categories_body=}")

            try:
                request_to_post_categories = requests.post(
                    url=post_categories_url,
                    headers=self.request_headers,
                    json=post_categories_body
                )
                request_to_post_categories.raise_for_status()
            except requests.exceptions.RequestException as e:
                if request_to_post_categories.status_code == 400 and request_to_post_categories.json() == {
                    "detail": "Field constraint error. Category id must be unique."
                }:
                    LOGGER.info(
                        f"Category {category} already exists in annotation. Skipping this request"
                    )
                else:
                    raise requests.exceptions.RequestException(
                        f"Failed request to 'annotation' - {e}"
                    ) from e

            else:
                LOGGER.debug(f"{request_to_post_categories.json()=}")

        return list(categories)

    def request_annotation_to_post_annotations(
        self, importjob_id_created
    ):
        file_id = self.s3_output_file_id

        annotations_post_url = f"{settings.annotation_service_url}annotation/{importjob_id_created}/{file_id}"

        pages = self.badgerdoc_format.badgerdoc_annotation.pages
        annotations_post_body = {
            "base_revision": None,
            "pipeline": 0,
            "pages": [page.dict() for page in pages],
            "validated": [],
            "failed_validation_pages": [],
            "similar_revisions": [],  # TODO: 'simial_revisions' will be replaced with 'links' with unknown format
            "categories": []  # TODO: what 'categories' are will be determined in future
        }
        LOGGER.debug(f"{annotations_post_url=}")
        LOGGER.debug(f"{pages=}")
        LOGGER.debug(f"{annotations_post_body=}")

        try:
            request_to_post_annotations = requests.post(
                url=annotations_post_url,
                headers=self.request_headers,
                json=annotations_post_body
            )
            request_to_post_annotations.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed request to 'annotation' - {e}"
            ) from e
        else:
            LOGGER.debug(f"{request_to_post_annotations.json()=}")

    def import_annotations_to_annotation_microservice(self):
        importjob_id_created = self.request_jobs_to_create_importjob()
        self.request_annotation_to_post_annotations(
            importjob_id_created
        )

        return importjob_id_created
