from typing import Dict, List

from botocore.client import BaseClient
from tenant_dependency import TenantData

from convert.converters.base_format.models.annotation import (
    BadgerdocAnnotation,
)
from convert.converters.base_format.models.manifest import Manifest
from convert.converters.base_format.models.tokens import Page
from convert.converters.labelstudio.badgerdoc_downloader import (
    BadgerdocDownloader,
)
from convert.converters.labelstudio.labelstudio_format import LabelStudioFormat
from convert.converters.labelstudio.labelstudio_uploader import (
    LabelStudioUploader,
)
from convert.converters.labelstudio.models.annotation import LabelStudioModel
from convert.converters.labelstudio.utils import combine
from convert.logger import get_logger
from convert.models.common import S3Path

LOGGER = get_logger(__file__)
LOGGER.setLevel("DEBUG")


class BadgerdocToLabelstudioConverter:
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
        s3_input_manifest: S3Path,
        s3_output_annotation: S3Path,
    ) -> None:
        downloader = BadgerdocDownloader(
            self.s3_client, s3_input_tokens, s3_input_manifest
        )
        (
            pages,
            annotations,
            manifest,
        ) = downloader.download()
        labelstudio_pages = self.convert_to_labelestudio(
            pages, annotations, manifest
        )
        labelstudio_combined_pages_data = combine(labelstudio_pages)
        labelstudio_combined = LabelStudioFormat()
        labelstudio_combined.labelstudio_data = labelstudio_combined_pages_data
        uploader = LabelStudioUploader(self.s3_client)
        uploader.upload(labelstudio_combined, s3_output_annotation)

    def convert_to_labelestudio(
        self,
        pages: List[Page],
        annotations: Dict[int, BadgerdocAnnotation],
        manifest: Manifest,
    ) -> List[LabelStudioModel]:
        labelstudio_pages = []
        for page in pages:
            annotation = None
            if page.page_num in annotations:
                annotation = annotations[page.page_num]
            labelstudio = LabelStudioFormat()
            labelstudio.from_badgerdoc(
                page,
                annotation,
                manifest,
                self.request_headers,
            )
            labelstudio_pages.append(labelstudio.labelstudio_data)
        return labelstudio_pages
