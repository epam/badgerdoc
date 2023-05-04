from pathlib import Path

import responses

from convert.converters.labelstudio.models.annotation import LabelStudioModel
from convert.converters.labelstudio.utils import combine

TEST_FILES_DIR = Path(__file__).parent / "data"


@responses.activate
def test_annotation_converter_no_taxonomies_and_document_labels() -> None:
    part_1 = LabelStudioModel.parse_file(TEST_FILES_DIR / "parts/p1.json")
    part_2 = LabelStudioModel.parse_file(TEST_FILES_DIR / "parts/p2.json")

    combination = combine([part_1, part_2])

    etalon_combination = LabelStudioModel.parse_file(
        TEST_FILES_DIR / "combined/labelstudio.json"
    )

    assert etalon_combination.__root__[0].annotations[0].result[0].value
    assert combination.__root__[0].annotations[0].result[0].value
    assert etalon_combination.__root__[0].annotations[0].result[1].value
    assert combination.__root__[0].annotations[0].result[1].value
    assert etalon_combination.__root__[0].annotations[0].result[2].value
    assert combination.__root__[0].annotations[0].result[2].value
    assert (
        etalon_combination.__root__[0].annotations[0].result[0].value.start
        == combination.__root__[0].annotations[0].result[0].value.start
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[0].value.end
        == combination.__root__[0].annotations[0].result[0].value.end
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[0].value.text
        == combination.__root__[0].annotations[0].result[0].value.text
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[0].value.labels
        == combination.__root__[0].annotations[0].result[0].value.labels
    )

    assert (
        etalon_combination.__root__[0].annotations[0].result[1].value.start
        == combination.__root__[0].annotations[0].result[1].value.start
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[1].value.end
        == combination.__root__[0].annotations[0].result[1].value.end
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[1].value.text
        == combination.__root__[0].annotations[0].result[1].value.text
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[1].value.labels
        == combination.__root__[0].annotations[0].result[1].value.labels
    )

    assert (
        etalon_combination.__root__[0].annotations[0].result[2].value.start
        == combination.__root__[0].annotations[0].result[2].value.start
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[2].value.end
        == combination.__root__[0].annotations[0].result[2].value.end
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[2].value.text
        == combination.__root__[0].annotations[0].result[2].value.text
    )
    assert (
        etalon_combination.__root__[0].annotations[0].result[2].value.labels
        == combination.__root__[0].annotations[0].result[2].value.labels
    )
