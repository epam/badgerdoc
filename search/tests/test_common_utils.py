import enum

import pytest

import search.common_utils as utils


@pytest.mark.unittest
def test_enum_generator():
    fields = ["text", "numeric"]
    enum_ = utils.enum_generator(fields, "abc")
    assert enum_.TEXT == "text"
    assert enum_.NUMERIC == "numeric"
    assert type(enum_) == enum.EnumMeta


@pytest.mark.unittest
def test_get_properties():
    index_settings = {"mappings": {"properties": {"job": 1}}}
    assert utils.get_mapping_fields(index_settings) == {"job": 1}
