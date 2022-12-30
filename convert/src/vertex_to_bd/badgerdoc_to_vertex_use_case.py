import tempfile
from pathlib import Path
from typing import NamedTuple, Optional

from src.vertex_to_bd.labelstudio_format import LabelStudioFormat

from .models import S3Path
from .models.bd_annotation_model import BadgerdocAnnotation
from .models.bd_tokens_model import Page


class BadgerdocData(NamedTuple):
    page: Page
    annotation: Optional[BadgerdocAnnotation]


class BDToVertexConvertUseCase:
    def __init__(
        self,
        s3_client=None,
    ) -> None:
        self.s3_client = s3_client
        self.labelstudio_format = LabelStudioFormat()

    def execute(
        self,
        s3_input_tokens: S3Path,
        s3_input_annotations: S3Path,
        s3_output_annotation: S3Path,
    ) -> None:
        (
            badgerdoc_page,
            badgerdoc_annotations,
        ) = self.download_badgerdoc_from_s3(
            s3_input_tokens,
            s3_input_annotations,
        )
        self.labelstudio_format.from_badgerdoc(
            badgerdoc_page, badgerdoc_annotations
        )
        self.upload_labelstudio_to_s3(s3_output_annotation)

    def download_badgerdoc_from_s3(
        self,
        s3_input_tokens,
        s3_input_annotations,
    ) -> BadgerdocData:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)
            input_tokens = tmp_dir / Path(s3_input_tokens.path).name

            self.s3_client.download_file(
                s3_input_tokens.bucket,
                s3_input_tokens.path,
                str(input_tokens),
            )

            page = Page.parse_file(input_tokens)
            return BadgerdocData(page=page, annotation=None)

    def upload_labelstudio_to_s3(
        self,
        s3_output_annotation: S3Path,
    ):
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)

            badgerdoc_annotations_path = tmp_dir / Path(
                "labelstudio_format.json"
            )
            self.labelstudio_format.export_json(badgerdoc_annotations_path)
            self.s3_client.upload_file(
                str(badgerdoc_annotations_path),
                s3_output_annotation.bucket,
                s3_output_annotation.path,
            )
