import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from botocore.client import BaseClient
from botocore.exceptions import ClientError
from fastapi import HTTPException

from convert.converters.base_format.models import annotation_practic
from convert.converters.base_format.models.annotation import (
    BadgerdocAnnotation,
)
from convert.converters.base_format.models.manifest import Manifest
from convert.converters.base_format.models.tokens import Page
from convert.converters.labelstudio.annotation_converter_practic import (
    AnnotationConverterToTheory,
)
from convert.logger import get_logger
from convert.models.common import S3Path

LOGGER = get_logger(__file__)
LOGGER.setLevel("DEBUG")


class BadgerdocDownloader:
    def __init__(self, s3_client: BaseClient, s3_input_tokens: S3Path, s3_input_manifest: S3Path):
        self.s3_input_tokens = s3_input_tokens
        self.s3_input_manifest = s3_input_manifest
        self.s3_client = s3_client

    def download(
        self,
    ) -> Tuple[List[Page], Dict[int, BadgerdocAnnotation], Manifest]:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)

            pages = self.get_token_pages(tmp_dir)
            manifest = self.get_manifest(tmp_dir)
            annotations = self.get_annotations(manifest, tmp_dir)

            return pages, annotations, manifest

    def get_token_pages(self, tmp_dir) -> List[Page]:
        token_page_files = self.download_all_token_pages(self.s3_input_tokens, tmp_dir)
        pages = []
        for token_page_file in token_page_files:
            pages.append(Page.parse_file(token_page_file))
        return pages

    def get_manifest(self, tmp_dir) -> Manifest:
        manifest_file = self.download_file_from_s3(
            self.s3_input_manifest, tmp_dir
        )
        return Manifest.parse_file(tmp_dir / manifest_file.name)

    def get_annotations(self, manifest: Manifest, tmp_dir) -> Dict[int, BadgerdocAnnotation]:
        annotation_files = self.download_annotations(
            manifest_s3_path=self.s3_input_manifest,
            manifest=manifest,
            tmp_dir=tmp_dir
        )
        annotations = {}
        for page_num, annotation_file in annotation_files.items():
            annotations[int(page_num)] = AnnotationConverterToTheory(
                practic_annotations=annotation_practic.BadgerdocAnnotation.parse_file(  # noqa
                    annotation_file
                )
            ).convert()
        return annotations

    def download_all_token_pages(self, s3_path: S3Path, tmp_dir: Path) -> List[Path]:
        response = self.s3_client.list_objects(Bucket=s3_path.bucket, Prefix=s3_path.path)
        pages = (obj['Key'] for obj in response['Contents'])
        page_files = []
        for page in pages:
            page_path = S3Path(bucket=s3_path.bucket, path=f"{page}")
            page_files.append(self.download_file_from_s3(s3_path=page_path, tmp_dir=tmp_dir))
        return page_files

    def download_annotations(self, manifest_s3_path: S3Path, manifest: Manifest, tmp_dir: Path) -> Dict[str, S3Path]:
        pages = {}
        for page_num, page_file in manifest.pages.items():
            page_s3_path = self.form_absolute_path_for_annotation(manifest_s3_path, page_file)
            pages[page_num] = self.download_file_from_s3(page_s3_path, tmp_dir)
        return pages

    def form_absolute_path_for_annotation(self, manifest_s3_path: S3Path, page_file: str) -> S3Path:
        absolute_path = f"{Path(manifest_s3_path.path).parent}/{page_file}.json"
        return S3Path(bucket=manifest_s3_path.bucket, path=absolute_path)

    def download_file_from_s3(self, s3_path: S3Path, tmp_dir: Path) -> Path:
        local_file_path = tmp_dir / Path(s3_path.path).name
        try:
            self.s3_client.download_file(
                s3_path.bucket,
                s3_path.path,
                str(local_file_path),
            )
        except ClientError as e:
            LOGGER.exception(
                "Cannot download file from S3: bucket %s path %s",
                s3_path.bucket,
                s3_path.path,
            )
            raise HTTPException(
                status_code=404,
                detail="Error during file fetching: file not found",
            ) from e
        return local_file_path
