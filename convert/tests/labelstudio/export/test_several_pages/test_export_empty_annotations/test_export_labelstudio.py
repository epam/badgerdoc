from pathlib import Path

import responses
from pydantic import BaseModel

from convert.converters.base_format.models import manifest
from convert.converters.base_format.models.tokens import Page
from convert.converters.labelstudio.badgerdoc_to_labelstudio_converter import (
    BadgerdocToLabelstudioConverter,
)
from convert.converters.labelstudio.utils import combine

TEST_FILES_DIR = Path(__file__).parent / "data_with_empty_annotations"


@responses.activate
def test_on_empty_annotations():
    responses.post(
        "http://dev2.badgerdoc.com/api/v1/annotation/"
        "jobs/1070/categories/search",
        json={"data": []},
    )
    tokens_test_1_page = Page.parse_file(
        TEST_FILES_DIR / "badgerdoc/tokens/1.json"
    )
    tokens_test_2_page = Page.parse_file(
        TEST_FILES_DIR / "badgerdoc/tokens/2.json"
    )
    manifest_test = manifest.Manifest.parse_file(
        TEST_FILES_DIR / "badgerdoc/annotation/manifest.json"
    )

    class MockToken(BaseModel):
        token = ""

    converter = BadgerdocToLabelstudioConverter(
        s3_client=None, current_tenant="", token_data=MockToken()
    )
    labelstudios = converter.convert_to_labelestudio(
        [tokens_test_1_page, tokens_test_2_page], {}, manifest_test
    )
    labelstudio_combined = combine(labelstudios)
    assert labelstudio_combined.__root__[0].data.text == "One Two "
