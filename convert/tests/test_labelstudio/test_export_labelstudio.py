from pathlib import Path

import responses
from _pytest.monkeypatch import MonkeyPatch
from starlette.testclient import TestClient

from convert.converters.base_format.models import annotation_practic, manifest
from convert.converters.base_format.models.tokens import Page
from convert.converters.labelstudio import annotation_converter_practic
from convert.converters.labelstudio.badgerdoc_to_labelstudio_converter import (
    BadgerdocToLabelstudioConverter,
    LabelStudioFormat,
)
from convert.converters.labelstudio.models.annotation import LabelStudioModel

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "labelstudio_format.json"


def test_correctness_of_export_text_schema(
    test_app: TestClient, monkeypatch: MonkeyPatch
) -> None:
    test_request_payload = {
        "input_tokens": {"bucket": "test", "path": "files/926/ocr/1.json"},
        "input_annotation": {
            "bucket": "test",
            "path": "annotation/1763/926/"
            "1ae7876fd4d777d5b4e6dbd338b230d74aa4ff8d.json",
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

    monkeypatch.setattr(
        BadgerdocToLabelstudioConverter, "execute", lambda *args, **kw: ...
    )

    response = test_app.post(
        "/labelstudio/export",
        json=test_request_payload,
    )

    assert response.status_code == 201


@responses.activate
def test_annotation_converter_no_taxonomies_and_document_labels() -> None:
    responses.post(
        "http://dev2.badgerdoc.com/api/v1/annotation/"
        "jobs/1070/categories/search",
        json={"data": []},
    )

    tokens_test = Page.parse_file(
        TEST_FILES_DIR / "badgerdoc_etalon" / "tokens_test.json"
    )
    manifest_test = manifest.Manifest.parse_file(
        TEST_FILES_DIR / "badgerdoc_etalon" / "manifest.json"
    )
    page_annotation_file_name = f"{manifest_test.pages['1']}.json"
    annotations_test = (
        annotation_converter_practic.AnnotationConverterToTheory(
            annotation_practic.BadgerdocAnnotation.parse_file(
                TEST_FILES_DIR / "badgerdoc_etalon" / page_annotation_file_name
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
        TEST_FILES_DIR / "labelstudio_format.json"
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


@responses.activate
def test_annotation_converter_case_without_export_labelstudio():
    responses.post(
        "http://dev2.badgerdoc.com/api/v1/annotation/"
        "jobs/1070/categories/search",
        json={"data": []},
    )
    tokens_test = Page.parse_file(
        TEST_FILES_DIR
        / "badgerdoc_etalon"
        / "tokens_test_without_whitespaces.json"
    )
    manifest_test = manifest.Manifest.parse_file(
        TEST_FILES_DIR / "badgerdoc_etalon" / "manifest.json"
    )
    annotations_test = (
        annotation_converter_practic.AnnotationConverterToTheory(
            annotation_practic.BadgerdocAnnotation.parse_file(
                TEST_FILES_DIR
                / "badgerdoc_etalon"
                / "annotations_test_empty.json"
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
