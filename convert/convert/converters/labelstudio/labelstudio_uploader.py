import tempfile
from pathlib import Path

from botocore.client import BaseClient
from convert.converters.labelstudio.labelstudio_format import LabelStudioFormat
from convert.models.common import S3Path


class LabelStudioUploader:
    LABELSTUDIO_FILENAME = "ls_format.json"

    def __init__(self, s3_client: BaseClient):
        self.s3_client = s3_client

    def upload(
        self,
        labelstudio: LabelStudioFormat,
        s3_output_annotation: S3Path,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            badgerdoc_annotations_path = Path(tmp_dirname) / Path(
                self.LABELSTUDIO_FILENAME
            )
            labelstudio.export_json(badgerdoc_annotations_path)
            self.s3_client.upload_file(
                str(badgerdoc_annotations_path),
                s3_output_annotation.bucket,
                s3_output_annotation.path,
            )
