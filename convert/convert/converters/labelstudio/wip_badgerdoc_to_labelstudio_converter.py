import tempfile
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

import requests
from botocore.client import BaseClient
from fastapi import HTTPException, status
from tenant_dependency import TenantData

from convert.config import settings
from convert.converters.base_format.models import annotation_practic
from convert.converters.base_format.models.annotation import (
    BadgerdocAnnotation,
)
from convert.converters.base_format.models.manifest import Manifest
from convert.converters.base_format.models.tokens import BadgerdocToken, Page
from convert.converters.labelstudio.annotation_converter_practic import (
    AnnotationConverterToTheory,
)
from convert.logger import get_logger
from convert.models.common import S3Path
from convert.converters.labelstudio.utils import combine

from .models.annotation import (
    Annotation,
    Data,
    DocumentRelation,
    LabelStudioModel,
    Meta,
    ModelItem,
    ResultItem,
    Value,
)

LOGGER = get_logger(__file__)
LOGGER.setLevel("DEBUG")


class BadgerdocData(NamedTuple):
    page: Page
    annotation: BadgerdocAnnotation
    manifest: Manifest


class LabelStudioFormat:
    DEFAULT_ID_FOR_ONE_ANNOTATION = 1

    # TODO: support more than 1 page
    def __init__(self) -> None:
        self.labelstudio_data = LabelStudioModel()

    @staticmethod
    def form_token_text(token: BadgerdocToken) -> str:
        text = f"{token.previous or ''}{token.text}{token.after or ''}"
        return text

    def from_badgerdoc(
        self,
        badgerdoc_tokens: Page,
        badgerdoc_annotations: BadgerdocAnnotation,
        badgerdoc_manifest: Optional[Manifest],
        request_headers: Dict[str, str],
    ):
        text = "".join(
            [self.form_token_text(obj) for obj in badgerdoc_tokens.objs]
        )

        objs = self.convert_annotation_from_bd(
            badgerdoc_annotations, badgerdoc_tokens.objs, text
        )
        relations = self.convert_relation_from_bd(badgerdoc_annotations)
        document_links = (
            self.convert_document_links_from_bd(badgerdoc_manifest)
            if badgerdoc_manifest
            else []
        )
        document_labels = [
            {
                "id": document_label["value"],
                "name": document_label["value"],
                "parent": None,
            }
            for document_label in badgerdoc_manifest.categories
        ]
        job_id = badgerdoc_manifest.job_id
        categories_linked_with_taxonomies = (
            self.get_categories_linked_with_taxonomies(job_id, request_headers)
        )
        LOGGER.debug(
            "Got there categories linked to taxonomies: %s",
            categories_linked_with_taxonomies,
        )

        categories_to_taxonomy_mapping = self.create_categories_to_taxonomy_mapping(  # noqa
            job_id=job_id,
            categories_linked_with_taxonomies=categories_linked_with_taxonomies,  # noqa
            request_headers=request_headers,
        )
        annotation = Annotation(
            id=self.DEFAULT_ID_FOR_ONE_ANNOTATION, result=objs + relations
        )

        item = ModelItem(
            annotations=[annotation],
            predictions=[],
            data=Data(text=text),
            meta=Meta(
                labels=document_labels,
                relations=document_links,
                categories_to_taxonomy_mapping=categories_to_taxonomy_mapping,
            ),
        )

        self.labelstudio_data.__root__.append(item)

    @classmethod
    def convert_annotation_from_bd(
            cls, annotations: BadgerdocAnnotation, tokens: List[BadgerdocToken], text: str
    ) -> List[ResultItem]:
        objs = annotations.pages[0].objs
        result_items = []
        for obj in objs:
            if not obj.tokens:
                continue
            start = cls.get_begin_offset(tokens, obj.tokens)
            end = cls.get_end_offset(tokens, obj.tokens)
            tokens_text = text[start:end]
            item = ResultItem(
                id=obj.id,
                from_name="label",
                to_name="text",
                type="labels",
                origin="manual",
                value=Value(
                    start=start,
                    end=end,
                    text=tokens_text,
                    labels=[obj.category],
                ),
            )
            if obj.data.dataAttributes:
                item.value.taxons = [
                    obj.data.dataAttributes[0]["value"],
                ]
            else:
                item.value.taxons = [
                    None,
                ]

            result_items.append(item)
        return result_items

    @staticmethod
    def get_begin_offset(tokens: List[BadgerdocToken], token_ids: List[int]) -> int:
        token_id = min(token_ids)
        return tokens[token_id].offset.begin

    @staticmethod
    def get_end_offset(tokens: List[BadgerdocToken], token_ids: List[int]) -> int:
        token_id = max(token_ids)
        return tokens[token_id].offset.end

    def convert_relation_from_bd(
        self, annotations: BadgerdocAnnotation
    ) -> List[ResultItem]:
        objs = annotations.pages[0].objs
        result_items = []
        for obj in objs:
            if not obj.links:
                continue
            for link in obj.links:
                item = ResultItem(
                    from_id=obj.id,
                    to_id=link.to,
                    type="relation",
                    direction=self.form_link_direction(),
                    labels=[link.category_id],
                )
                result_items.append(item)
        return result_items

    @staticmethod
    def convert_document_links_from_bd(
        manifest: Manifest,
    ) -> List[DocumentRelation]:
        return [
            # converting from a model with same attributes
            DocumentRelation(**document_link.dict())
            for document_link in manifest.links_json
        ]

    @staticmethod
    def form_link_direction() -> str:
        # TODO: add logic for transformation link from badgerdoc format
        return "right"

    def export_json(self, path: Path):
        path.write_text(self.labelstudio_data.json())

    @staticmethod
    def get_categories_linked_with_taxonomies(
        job_id: int, request_headers: Dict[str, str]
    ) -> List[str]:
        annotations_get_categories_url = (
            f"{settings.annotation_service_url}jobs/{job_id}/categories/search"
        )
        annotations_get_categories_body = {
            "pagination": {"page_num": 1, "page_size": 100}
        }
        LOGGER.debug(
            "Making request to url %s to get all categories for job_id %s",
            annotations_get_categories_url,
            job_id,
        )

        try:
            request_to_get_categories = requests.post(
                url=annotations_get_categories_url,
                headers=request_headers,
                json=annotations_get_categories_body,
            )
            request_to_get_categories.raise_for_status()
        except requests.exceptions.RequestException as exception:
            LOGGER.exception(
                "Failed request to 'annotation' to get "
                "all categories for specific job"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed request to 'annotation' to get "
                "all categories for specific job",
            ) from exception

        LOGGER.debug(
            "Got this response from annotation service: %s",
            request_to_get_categories.json(),
        )
        all_categories_got = request_to_get_categories.json()["data"]
        categories_linked_with_taxonomies = [
            category["id"]
            for category in all_categories_got
            if category["data_attributes"]
        ]
        return categories_linked_with_taxonomies

    @staticmethod
    def get_corresponding_taxonomy_obj(
        job_id: int, category_id: str, request_headers: Dict[str, str]
    ) -> List[Dict[str, str]]:
        get_taxonomy_url = (
            f"{settings.taxonomy_service_url}taxonomy/"
            f"link_category/{job_id}/{category_id}"
        )
        LOGGER.debug(
            "Making request to url %s to get corresponding taxonomy",
            get_taxonomy_url,
        )

        try:
            request_to_get_taxonomy = requests.get(
                url=get_taxonomy_url,
                headers=request_headers,
            )
            request_to_get_taxonomy.raise_for_status()
        except requests.exceptions.RequestException as exception:
            LOGGER.exception(
                "Failed request to 'taxonomy' to get corresponding taxonomy"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed request to 'taxonomy' to "
                "get corresponding taxonomy",
            ) from exception
        response_content = request_to_get_taxonomy.json()
        LOGGER.debug(
            "Got this response from taxonomy service: %s", response_content
        )

        return [
            {"taxonomy_id": element["id"], "version": element["version"]}
            for element in response_content
        ]

    def create_categories_to_taxonomy_mapping(
        self, job_id, categories_linked_with_taxonomies, request_headers
    ):
        result = {}
        for category_id in categories_linked_with_taxonomies:
            taxonomy_objs = self.get_corresponding_taxonomy_obj(
                job_id=job_id,
                category_id=category_id,
                request_headers=request_headers,
            )
            for taxonomy_obj in taxonomy_objs:
                result.update({category_id: taxonomy_obj})
        return result

    @staticmethod
    def get_taxonomy_to_taxons_mapping(
        all_taxonomies_ids_used: List[str],
        request_headers: Dict[str, str],
    ) -> Dict[str, Any]:
        get_taxons_used_url = f"{settings.taxonomy_service_url}taxons/search"
        LOGGER.debug(
            "Making request to url %s to get all taxons used",
            get_taxons_used_url,
        )
        get_taxons_used_body = {
            "pagination": {"page_num": 1, "page_size": 100},
            "filters": [
                {
                    "field": "taxonomy_id",
                    "operator": "in",
                    "value": all_taxonomies_ids_used,
                }
            ],
        }

        try:
            request_to_get_taxons_used = requests.post(
                url=get_taxons_used_url,
                json=get_taxons_used_body,
                headers=request_headers,
            )
            request_to_get_taxons_used.raise_for_status()
        except requests.exceptions.RequestException as exception:
            LOGGER.exception("Failed request to 'taxonomy' to get taxons_used")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed request to 'taxonomy' to get taxons_used",
            ) from exception
        response_content = request_to_get_taxons_used.json()
        LOGGER.debug(
            "Got this response from taxonomy service: %s", response_content
        )

        result = {taxonomy_id: [] for taxonomy_id in all_taxonomies_ids_used}
        for taxon_obj in response_content["data"]:
            taxonomy_id_of_taxon = taxon_obj["taxonomy_id"]
            result[taxonomy_id_of_taxon].append(taxon_obj["id"])

        return result


class WipBadgerdocToLabelstudioConverter:
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
        downloader = BadgerdocDownloader(self.s3_client, s3_input_tokens, s3_input_manifest)
        (
            pages,
            annotations,
            manifest,
        ) = downloader.download()
        labelstudio_pages = self.convert_to_labelestudio(pages, annotations, manifest)
        labelstudio_combined_pages_data = combine(labelstudio_pages)
        labelstudio_combined = LabelStudioFormat()
        labelstudio_combined.labelstudio_data = labelstudio_combined_pages_data
        uploader = LabelStudioUploader(self.s3_client)
        uploader.upload(labelstudio_combined, s3_output_annotation)

    def convert_to_labelestudio(
            self,
            pages: List[Page],
            annotations: Dict[int, annotation_practic.BadgerdocAnnotation],
            manifest: Manifest
        ) -> List[LabelStudioModel]:
        labelstudio_pages = []
        for page in pages:
            labelstudio = LabelStudioFormat()
            labelstudio.from_badgerdoc(
                page,
                annotations[page.page_num],
                manifest,
                self.request_headers,
            )
            labelstudio_pages.append(labelstudio.labelstudio_data)
        return labelstudio_pages


class BadgerdocDownloader:
    def __init__(self, s3_client: BaseClient, s3_input_tokens: S3Path, s3_input_manifest: S3Path):
        self.s3_input_tokens = s3_input_tokens
        self.s3_input_manifest = s3_input_manifest
        self.s3_client = s3_client

    def download(
        self,
    ) -> Tuple[List[Page], Dict[int, annotation_practic.BadgerdocAnnotation], Manifest]:
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

    def get_annotations(self, manifest: Manifest, tmp_dir) -> Dict[int, annotation_practic.BadgerdocAnnotation]:
        annotation_files = self.download_annotations(
            manifest_s3_path=self.s3_input_manifest,
            manifest=manifest,
            tmp_dir=tmp_dir
        )
        annotations = {}
        for page_num, annotation_file in annotation_files.items():
            annotations[int(page_num)] = annotation_practic.BadgerdocAnnotation.parse_file(annotation_file)
            # annotation = AnnotationConverterToTheory(
            #     practic_annotations=annotation_practic.BadgerdocAnnotation.parse_file(  # noqa
            #         input_annotations
            #     )
            # ).convert()
        return annotations

    def download_all_token_pages(self, s3_path: S3Path, tmp_dir: Path) -> List[Path]:
        response = self.s3_client.list_objects(Bucket=s3_path.bucket, Prefix=s3_path.path)
        pages = (obj['Key'] for obj in response['Contents'])
        page_files = []
        for page in pages:
            page_path = S3Path(bucket=s3_path.bucket, path=f"{page}")
            page_files.append(self.download_file_from_s3(s3_path=page_path, tmp_dir=tmp_dir))
        return page_files

    def download_file_from_s3(self, s3_path: S3Path, tmp_dir: Path) -> Path:
        local_file_path = tmp_dir / Path(s3_path.path).name
        self.s3_client.download_file(
            s3_path.bucket,
            s3_path.path,
            str(local_file_path),
        )
        return local_file_path

    def download_annotations(self, manifest_s3_path: S3Path, manifest: Manifest, tmp_dir: Path) -> Dict[str, S3Path]:
        pages = {}
        for page_num, page_file in manifest.pages:
            page_s3_path = self.form_absolute_path_for_annotation(manifest_s3_path, page_file)
            pages[page_num] = self.download_file_from_s3(page_s3_path, tmp_dir)
        return pages

    def form_absolute_path_for_annotation(self, manifest_s3_path: S3Path, page_file: str) -> S3Path:
        absolute_path = f"{Path(manifest_s3_path.path).parent}/{page_file}.json"
        return S3Path(bucket=manifest_s3_path.bucket, path=absolute_path)


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
