import pytest

from search.config import settings


@pytest.mark.unittest
def test_no_slashes():
    settings.annotation_url = "foo"
    settings.annotation_categories = "bar"
    assert settings.annotation_categories_url == "foo/bar"


@pytest.mark.unittest
def test_many_slashes():
    settings.annotation_url = "foo.com///"
    settings.annotation_categories = "///bar"
    assert settings.annotation_categories_url == "foo.com/bar"
