from pathlib import Path

from convert.label_studio_to_badgerdoc.badgerdoc_format import (
    annotation_converter_practic,
)
from convert.label_studio_to_badgerdoc.labelstudio_format.label_studio_format import (
    LabelStudioFormat,
)
from convert.label_studio_to_badgerdoc.models import (
    bd_annotation_model_practic,
    bd_manifest_model_practic,
)
from convert.label_studio_to_badgerdoc.models.bd_tokens_model import Page
from convert.label_studio_to_badgerdoc.models.label_studio_models import (
    LabelStudioModel,
)

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "label_studio_format.json"


def test_annotation_converter():
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
