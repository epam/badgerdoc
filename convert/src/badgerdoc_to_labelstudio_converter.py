import tempfile
from pathlib import Path
from typing import NamedTuple

from botocore.client import BaseClient
from tenant_dependency import TenantData

from src.badgerdoc_format.annotation_converter_practic import (
    AnnotationConverterToTheory,
)
from src.labelstudio_format.ls_format import LabelStudioFormat
from src.logger import get_logger

from .models.common  import S3Path 
from .badgerdoc_format import bd_annotation_model_practic
from .badgerdoc_format.bd_annotation_model import BadgerdocAnnotation
from .badgerdoc_format.bd_manifest_model_practic import Manifest
from .badgerdoc_format.bd_tokens_model import Page

LOGGER = get_logger(__file__)
LOGGER.setLevel("DEBUG")


class BadgerdocData(NamedTuple):
    page: Page
    annotation: BadgerdocAnnotation
    manifest: Manifest


class BadgerdocToLabelstudioConverter:
    LABELSTUDIO_FILENAME = "ls_format.json"

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
        self.ls_format = LabelStudioFormat()

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
        ) = self.download(
            s3_input_tokens, s3_input_annotations, s3_input_manifest
        )
        self.ls_format.from_badgerdoc(
            badgerdoc_page,
            badgerdoc_annotations,
            badgerdoc_manifest,
            self.request_headers,
        )
        self.upload(s3_output_annotation)

    def download(
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
            input_manifest = self.download_file_from_s3(
                s3_input_manifest, tmp_dir
            )
            LOGGER.debug("input_manifest: %s", input_manifest.read_text())

            page = Page.parse_file(input_tokens)
            annotation = AnnotationConverterToTheory(
                practic_annotations=bd_annotation_model_practic.BadgerdocAnnotation.parse_file(
                    input_annotations
                )
            ).convert()
            manifest = Manifest.parse_file(input_manifest)
            return BadgerdocData(
                page=page, annotation=annotation, manifest=manifest
            )

    def download_file_from_s3(self, s3_path: S3Path, tmp_dir: Path) -> Path:
        local_file_path = tmp_dir / Path(s3_path.path).name
        self.s3_client.download_file(
            s3_path.bucket,
            s3_path.path,
            str(local_file_path),
        )
        return local_file_path

    def upload(
        self,
        s3_output_annotation: S3Path,
    ):
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)

            badgerdoc_annotations_path = tmp_dir / Path(
                self.LABELSTUDIO_FILENAME
            )
            self.ls_format.export_json(badgerdoc_annotations_path)
            self.s3_client.upload_file(
                str(badgerdoc_annotations_path),
                s3_output_annotation.bucket,
                s3_output_annotation.path,
            )
