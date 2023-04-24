from pathlib import Path

import responses

from convert.converters.base_format.models import annotation_practic, manifest
from convert.converters.base_format.models.tokens import Page
from convert.converters.labelstudio import annotation_converter_practic
from convert.converters.labelstudio.badgerdoc_to_labelstudio_converter import (
    LabelStudioFormat,
)

TEST_FILES_DIR = Path(__file__).parent / "data"


@responses.activate
def test_annotation_converter_case_without_export_labelstudio():
    responses.post(
        "http://dev2.badgerdoc.com/api/v1/annotation/"
        "jobs/1070/categories/search",
        json={"data": []},
    )
    tokens_test = Page.parse_file(
        TEST_FILES_DIR / "badgerdoc/tokens/tokens_without_whitespaces.json"
    )
    manifest_test = manifest.Manifest.parse_file(
        TEST_FILES_DIR / "badgerdoc/annotation/manifest.json"
    )
    annotations_test = (
        annotation_converter_practic.AnnotationConverterToTheory(
            annotation_practic.BadgerdocAnnotation.parse_file(
                TEST_FILES_DIR / "badgerdoc/annotation/annotations_empty.json"
            )
        ).convert()
    )

    ls_format_test = LabelStudioFormat()
    ls_format_test.from_badgerdoc(
        badgerdoc_annotations=annotations_test,
        badgerdoc_tokens=tokens_test,
        badgerdoc_manifest=manifest_test,
        request_headers={},
    )
    assert ls_format_test.labelstudio_data.__root__[0].data.text == "All "
