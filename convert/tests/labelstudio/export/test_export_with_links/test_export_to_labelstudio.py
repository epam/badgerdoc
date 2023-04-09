from pathlib import Path

import responses

from convert.converters.base_format.models import annotation_practic, manifest
from convert.converters.base_format.models.tokens import Page
from convert.converters.labelstudio import annotation_converter_practic
from convert.converters.labelstudio.badgerdoc_to_labelstudio_converter import (
    LabelStudioFormat,
)
from convert.converters.labelstudio.models.annotation import LabelStudioModel

TEST_FILES_DIR = Path(__file__).parent / "data_annotations_with_links"


@responses.activate
def test_annotation_converter_no_taxonomies_and_document_labels() -> None:
    responses.post(
        "http://dev2.badgerdoc.com/api/v1/annotation/"
        "jobs/2190/categories/search",
        json={"data": []},
    )

    tokens_test = Page.parse_file(
        TEST_FILES_DIR / "badgerdoc/tokens/1.json"
    )
    manifest_test = manifest.Manifest.parse_file(
        TEST_FILES_DIR / "badgerdoc/annotation/manifest.json"
    )
    annotations_test = (
        annotation_converter_practic.AnnotationConverterToTheory(
            annotation_practic.BadgerdocAnnotation.parse_file(
                TEST_FILES_DIR / "badgerdoc/annotation/fixed.json"
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
    labelstudio_model_test = ls_format_test.labelstudio_data
    labelstudio_model_etalon = LabelStudioModel.parse_file(
        TEST_FILES_DIR / "labelstudio.json"
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[0].value.start
        == labelstudio_model_test.__root__[0].annotations[0].result[0].value.start
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[0].value.end
        == labelstudio_model_test.__root__[0].annotations[0].result[0].value.end
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[0].value.text
        == labelstudio_model_test.__root__[0].annotations[0].result[0].value.text
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[0].value.labels
        == labelstudio_model_test.__root__[0].annotations[0].result[0].value.labels
    )

    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[1].value.start
        == labelstudio_model_test.__root__[0].annotations[0].result[1].value.start
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[1].value.end
        == labelstudio_model_test.__root__[0].annotations[0].result[1].value.end
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[1].value.text
        == labelstudio_model_test.__root__[0].annotations[0].result[1].value.text
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[1].value.labels
        == labelstudio_model_test.__root__[0].annotations[0].result[1].value.labels
    )

    assert set(
        str(relation)
        for relation in labelstudio_model_etalon.__root__[0].meta.relations
    ) == set(
        str(relation)
        for relation in labelstudio_model_test.__root__[0].meta.relations
    )
