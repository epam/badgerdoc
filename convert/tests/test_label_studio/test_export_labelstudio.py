from pathlib import Path

import pytest
import responses

from src.label_studio_to_badgerdoc.badgerdoc_format import (
    annotation_converter_practic,
)
from src.label_studio_to_badgerdoc.badgerdoc_to_labelstudio_converter import (
    BadgerdocToLabelstudioConverter,
)
from src.label_studio_to_badgerdoc.labelstudio_format.label_studio_format import (
    LabelStudioFormat,
)
from src.label_studio_to_badgerdoc.models import (
    bd_annotation_model_practic,
    bd_manifest_model_practic,
)
from src.label_studio_to_badgerdoc.models.bd_tokens_model import Page
from src.label_studio_to_badgerdoc.models.label_studio_models import (
    LabelStudioModel,
)

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "label_studio_format.json"


def test_correctness_of_export_text_schema(test_app, monkeypatch):
    test_request_payload = {
        "input_tokens": {"bucket": "test", "path": "files/926/ocr/1.json"},
        "input_annotation": {
            "bucket": "test",
            "path": "annotation/1763/926/1ae7876fd4d777d5b4e6dbd338b230d74aa4ff8d.json",
        },
        "input_manifest": {
            "bucket": "test",
            "path": "annotation/1763/926/manifest.json",
        },
        "output_annotation": {
            "bucket": "test",
            "path": "test_converter/out.json",
        },
    }

    def mock_execute(*args, **kwargs):
        pass

    monkeypatch.setattr(BadgerdocToLabelstudioConverter, "execute", mock_execute)

    response = test_app.post(
        "/label_studio/export",
        json=test_request_payload,
    )

    assert response.status_code == 201


@responses.activate
def test_annotation_converter_case_without_taxonomies_and_document_labels():
    responses.post(
        "http://dev2.badgerdoc.com/api/v1/annotation/jobs/1070/categories/search",
        json={"data": []},
    )

    tokens_test = Page.parse_file(
        TEST_FILES_DIR / "badgerdoc_etalon" / "tokens_test.json"
    )
    manifest_test = bd_manifest_model_practic.Manifest.parse_file(
        TEST_FILES_DIR / "badgerdoc_etalon" / "manifest.json"
    )
    page_annotation_file_name = f"{manifest_test.pages['1']}.json"
    annotations_test = (
        annotation_converter_practic.AnnotationConverterToTheory(
            bd_annotation_model_practic.BadgerdocAnnotation.parse_file(
                TEST_FILES_DIR / "badgerdoc_etalon" / page_annotation_file_name
            )
        ).convert()
    )

    labelstudio_format_test = LabelStudioFormat()
    labelstudio_format_test.from_badgerdoc(
        badgerdoc_annotations=annotations_test,
        badgerdoc_tokens=tokens_test,
        badgerdoc_manifest=manifest_test,
        request_headers={}
    )
    labelstudio_model_test = labelstudio_format_test.labelstudio_data

    labelstudio_model_etalon = LabelStudioModel.parse_file(
        TEST_FILES_DIR / "label_studio_format.json"
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[0].value
        == labelstudio_model_test.__root__[0].annotations[0].result[0].value
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[1].value
        == labelstudio_model_test.__root__[0].annotations[0].result[1].value
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[2].value
        == labelstudio_model_test.__root__[0].annotations[0].result[2].value
    )
    assert set(
        str(relation)
        for relation in labelstudio_model_etalon.__root__[0].meta.relations
    ) == set(
        str(relation)
        for relation in labelstudio_model_test.__root__[0].meta.relations
    )
