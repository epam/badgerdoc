import json
import tempfile
from pathlib import Path

import boto3

from .models import S3Path
from .pdf_renderer import PDFRenderer
from .plain_text_converter import PlainTextToBadgerdocTokenConverter


class VertexToBDConvertUseCase:
    def __init__(
        self,
        plain_text_converter: PlainTextToBadgerdocTokenConverter,
        pdf_renderer: PDFRenderer,
        annotation_converter=None,
        s3_client=None,
    ) -> None:
        self.plain_text_converter = plain_text_converter
        self.pdf_renderer = pdf_renderer
        self.annotation_converter = annotation_converter
        self.s3_client = s3_client

    def execute(
        self,
        s3_input_annotation: S3Path,
        s3_output_pdf: S3Path,
        s3_output_tokens: S3Path,
        s3_output_annotation: S3Path,  # TODO
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)
            input_file = tmp_dirname / Path(s3_input_annotation.path).name
            self.s3_client.download_file(s3_input_annotation.bucket,
                s3_input_annotation.path, str(input_file)
            )

            badgerdoc_tokens_path = tmp_dirname / "badgerdoc_tokens.json"
            pdf_path = tmp_dirname / "badgerdoc_render.pdf"
            self.convert(input_file, badgerdoc_tokens_path, pdf_path)

            self.s3_client.upload_file(
                str(badgerdoc_tokens_path),
                s3_output_tokens.bucket,
                s3_output_tokens.path
            )

            self.s3_client.upload_file(
                str(pdf_path),
                s3_output_pdf.bucket,
                s3_output_pdf.path
            )

    def convert(
        self, input_file: Path, badgerdoc_tokens_path: Path, pdf_path: Path
    ) -> None:
        input_data = json.loads(input_file.read_text())

        # TODO: process more than 1 elem
        for annotation in input_data:
            text = annotation["data"]["text"]
            badgerdoc_tokens = self.plain_text_converter.convert(text)
            badgerdoc_tokens_path.write_text(badgerdoc_tokens.json())

            self.pdf_renderer.render_tokens(badgerdoc_tokens.objs, pdf_path)
            break
