import tempfile
from pathlib import Path
from typing import NamedTuple

from botocore.client import BaseClient
from convert.label_studio_to_badgerdoc.badgerdoc_format.annotation_converter_practic import (
    AnnotationConverterToTheory,
)
from convert.label_studio_to_badgerdoc.labelstudio_format import (
    LabelStudioFormat,
)
from convert.logger import get_logger
from tenant_dependency import TenantData

from .models import S3Path, bd_annotation_model_practic
from .models.bd_annotation_model import BadgerdocAnnotation
from .models.bd_manifest_model_practic import Manifest
from .models.bd_tokens_model import Page

LOGGER = get_logger(__file__)
LOGGER.setLevel("DEBUG")


class BadgerdocData(NamedTuple):
    page: Page
    annotation: BadgerdocAnnotation
    manifest: Manifest


class BDToLabelStudioConvertUseCase:
    labelstudio_format = LabelStudioFormat()

    def __init__(
        self,
        s3_client: BaseClient,
        current_tenant: str,
        token_data: TenantData,
    ) -> None:
        self.s3_client = s3_client
        self.current_tenant = current_tenant
        self.token_data = token_data
        self.request_headers = {
            "X-Current-Tenant": self.current_tenant,
            "Authorization": f"Bearer {self.token_data.token}",
        }

    def execute(
        self,
        s3_input_tokens: S3Path,
        s3_input_annotations: S3Path,
        s3_input_manifest: S3Path,
        s3_output_annotation: S3Path,
    ) -> None:
        (
            badgerdoc_page,
            badgerdoc_annotations,
            badgerdoc_manifest,
        ) = self.download_badgerdoc_from_s3(
            s3_input_tokens, s3_input_annotations, s3_input_manifest
        )
        self.labelstudio_format.from_badgerdoc(
            badgerdoc_page,
            badgerdoc_annotations,
            badgerdoc_manifest,
            self.request_headers,
        )
        self.upload_labelstudio_to_s3(s3_output_annotation)

    def download_badgerdoc_from_s3(
        self,
        s3_input_tokens: S3Path,
        s3_input_annotations: S3Path,
        s3_input_manifest: S3Path,
    ) -> BadgerdocData:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)

            input_tokens = self.download_file_from_s3(s3_input_tokens, tmp_dir)
            input_annotations = self.download_file_from_s3(
                s3_input_annotations, tmp_dir
            )
            input_manifest = self.download_file_from_s3(s3_input_manifest, tmp_dir)
            LOGGER.debug("input_manifest: %s", input_manifest.read_text())

            page = Page.parse_file(input_tokens)
            annotation = AnnotationConverterToTheory(
                practic_annotations=bd_annotation_model_practic.BadgerdocAnnotation.parse_file(
                    input_annotations
                )
            ).convert()
            manifest = Manifest.parse_file(input_manifest)
            return BadgerdocData(page=page, annotation=annotation, manifest=manifest)

    def download_file_from_s3(self, s3_path: S3Path, tmp_dir: Path) -> Path:
        local_file_path = tmp_dir / Path(s3_path.path).name
        self.s3_client.download_file(
            s3_path.bucket,
            s3_path.path,
            str(local_file_path),
        )
        return local_file_path

    def upload_labelstudio_to_s3(
        self,
        s3_output_annotation: S3Path,
    ):
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)

            badgerdoc_annotations_path = tmp_dir / Path("labelstudio_format.json")
            self.labelstudio_format.export_json(badgerdoc_annotations_path)
            self.s3_client.upload_file(
                str(badgerdoc_annotations_path),
                s3_output_annotation.bucket,
                s3_output_annotation.path,
            )
