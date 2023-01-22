from pathlib import Path
from src.label_studio_to_badgerdoc.models.label_studio_models import (
    LabelStudioModel,
)
from src.label_studio_to_badgerdoc.labelstudio_format.labelstudio_format import LabelStudioFormat
from src.label_studio_to_badgerdoc.badgerdoc_format import annotation_converter_practic
from src.label_studio_to_badgerdoc.models import bd_annotation_model_practic
from src.label_studio_to_badgerdoc.models.bd_tokens_model import Page

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "label_studio_format.json"


def test_annotation_converter():
    tokens_test = Page.parse_file(
        TEST_FILES_DIR / "badgerdoc_etalon" / "tokens_test.json"
    )
    annotations_test = annotation_converter_practic.AnnotationConverterToTheory(
        bd_annotation_model_practic.BadgerdocAnnotation.parse_file(
        TEST_FILES_DIR / "badgerdoc_etalon" / "annotations_test.json"
        )
    ).convert()

    labelstudio_format_test = LabelStudioFormat()
    labelstudio_format_test.from_badgerdoc(
        badgerdoc_annotations=annotations_test, badgerdoc_tokens=tokens_test
    )
    labelstudio_model_test = labelstudio_format_test.labelstudio_data

    labelstudio_model_etalon = LabelStudioModel.parse_file(
        TEST_FILES_DIR / "label_studio_format.json"
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[0].value ==
        labelstudio_model_test.__root__[0].annotations[0].result[0].value
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[1].value ==
        labelstudio_model_test.__root__[0].annotations[0].result[1].value
    )
    assert (
        labelstudio_model_etalon.__root__[0].annotations[0].result[2].value ==
        labelstudio_model_test.__root__[0].annotations[0].result[2].value
    )
