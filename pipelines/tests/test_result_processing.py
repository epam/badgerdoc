"""Testing src/result_processing.py."""
from unittest.mock import MagicMock, patch

import pytest
from minio import S3Error

import src.result_processing as processing


def test_merge_outputs():
    """Testing merge of ModelOutput."""
    page_1 = processing.Page(
        page_num=1, size=processing.Size(width=2, height=4), objs=[]
    )
    page_2 = processing.Page(
        page_num=2, size=processing.Size(width=4, height=6), objs=[]
    )
    page_3 = processing.Page(
        page_num=3, size=processing.Size(width=10, height=20), objs=[]
    )
    model_1 = processing.ModelOutput(pages=[page_1, page_2])
    model_2 = processing.ModelOutput(pages=[page_1, page_3])
    res = model_1.merge([model_1, model_2])
    assert len(res.pages) == 3
    for page, num in zip(
        res.pages,
        (
            (1, {"width": 2.0, "height": 4.0}),
            (2, {"width": 4.0, "height": 6.0}),
            (3, {"width": 10.0, "height": 20.0}),
        ),
    ):
        assert page.page_num == num[0]
        assert page.size == num[1]


def test_merge_outputs_no_pages():
    """Testing merge of ModelOutput when there's no pages."""
    model = processing.ModelOutput(pages=[])
    assert model.merge([model]) is None


def test_merge_pages():
    """Testing merge of Page."""
    page_1 = processing.Page(
        page_num=1, size=processing.Size(width=1, height=2), objs=[]
    )
    page_2 = processing.Page(
        page_num=2, size=processing.Size(width=2, height=4), objs=[]
    )
    res = page_1.merge([page_1, page_2])
    assert res.page_num == 1
    assert res.size == {"width": 1, "height": 2}


def test_merge_pages_no_pages():
    """Testing merge of Page when pages are not provided."""
    assert processing.Page.merge([]) is None


def test_group_pages_by_page_num():
    """Testing group_pages_by_page_num of Page."""
    page_1 = processing.Page(
        page_num=1, size=processing.Size(width=1, height=2), objs=[]
    )
    page_2 = processing.Page(
        page_num=1, size=processing.Size(width=2, height=4), objs=[]
    )
    page_3 = processing.Page(
        page_num=2, size=processing.Size(width=4, height=6), objs=[]
    )
    res = page_1.group_pages_by_page_num([page_1, page_2, page_3])
    assert len(res) == 2
    assert res[1] == [page_1, page_2]
    assert res[2] == [page_3]


def test_unite_geometry_objects():
    """Testing unite_geometry_objects of GeometryObject."""
    r_obj_1 = processing.GeometryObject(
        id=1,
        bbox=(1, 1, 1, 1),
        category=1,
        links=[{"category": "1", "to": 1, "page_num": 1}],
    )
    r_obj_2 = processing.GeometryObject(
        id=2, bbox=(1, 1, 1, 1), category=2, children=[3]
    )
    r_obj_3 = processing.GeometryObject(id=3, bbox=(1, 1, 1, 1), category=3)
    obj_1 = processing.GeometryObject(
        id="some_uiid_1",
        bbox=(1, 1, 1, 1),
        category=1,
        links=[{"category": "some_cat", "to": "some_uiid_1", "page_num": 1}],
    )
    obj_2 = processing.GeometryObject(
        id="some_uiid_2",
        bbox=(1, 1, 1, 1),
        category=2,
        children=["some_uiid_3"],
    )
    obj_3 = processing.GeometryObject(
        id="some_uiid_3", bbox=(1, 1, 1, 1), category=3
    )
    res = obj_1.unite_geometry_objects([obj_1, obj_2, obj_3], id_start=1)
    assert res == [r_obj_1, r_obj_2, r_obj_3]


def test_unite_geometry_objects_same_ids():
    """Testing unite_geometry_objects of GeometryObject when ids are the same
    and it's needed to be merged."""
    obj_1 = processing.GeometryObject(
        id=1, bbox=(1, 1, 1, 1), category=1, data={"a": 1}
    )
    obj_2 = processing.GeometryObject(
        id=1, bbox=(1, 1, 1, 1), category=1, data={"a": 2, "b": 3}
    )
    obj_3 = processing.GeometryObject(id=2, bbox=(2, 2, 2, 2), category=3)
    res = obj_1.unite_geometry_objects([obj_1, obj_2, obj_3], id_start=1)
    expected = [
        processing.GeometryObject(
            id=1, bbox=(1, 1, 1, 1), category=1, data={"a": 2, "b": 3}
        ),
        obj_3,
    ]
    assert res == expected


def test_group_objs_by_id():
    """Testing group_objs_by_id of GeometryObject."""
    obj_1 = processing.GeometryObject(id=1, bbox=(1, 1, 1, 1), category="some")
    obj_2 = processing.GeometryObject(id=1, bbox=(1, 1, 1, 1), category="some")
    obj_3 = processing.GeometryObject(
        id="asd", bbox=(1, 1, 1, 1), category="some"
    )
    obj_4 = processing.GeometryObject(
        id="asd", bbox=(1, 1, 1, 1), category="some"
    )
    res = processing.GeometryObject.group_objs_by_id(
        [obj_1, obj_2, obj_3, obj_4]
    )
    assert len(res) == 2
    assert res[1] == [obj_1, obj_2]
    assert res["asd"] == [obj_3, obj_4]


def test_merge_geometry_objects():
    """Testing merge of GeometryObject."""
    obj_1 = processing.GeometryObject(
        id="asd", bbox=(1, 1, 1, 1), data={"foo": 1}, category="some"
    )
    obj_2 = processing.GeometryObject(
        id="asd", bbox=(1, 1, 1, 1), data={"foo": 2, "bar": 3}, category="some"
    )
    obj_3 = processing.GeometryObject(
        id="asd",
        bbox=(1, 1, 1, 1),
        data=None,
        category="some",
        children=["some_children_id"],
    )
    res = processing.GeometryObject.merge([obj_1, obj_2, obj_3])
    assert res == processing.GeometryObject(
        id=0,
        bbox=(1, 1, 1, 1),
        data={"foo": 2, "bar": 3},
        children=["some_children_id"],
        category="some",
    )


def test_merge_geometry_objects_no_objects_provided():
    """Objects for merge are not provided."""
    with pytest.raises(ValueError, match="No GeometryObjects to merge"):
        assert processing.GeometryObject.merge([])


@pytest.mark.parametrize(
    ["job_id", "file_id", "expected"],
    [
        (1, 1, "foobar/ann/annotation/1/1"),
        ("1", "2", "foobar/ann/annotation/1/2"),
        (1, "asd", "foobar/ann/annotation/1/asd"),
    ],
)
def test_get_annotation_uri(job_id, file_id, expected):
    """Testing get_annotation_uri."""
    with patch("src.result_processing.config.ANNOTATION_URI", "foobar/ann"):
        assert processing.get_annotation_uri(job_id, file_id) == expected


@pytest.mark.parametrize(
    ["path_", "expected"],
    [
        ("foo/bar/baz.json", "baz"),
        ("foo/bar/baz.tar.gz", "baz"),
        ("foo/bar/baz", "baz"),
        ("foo/bar/baz/", "baz"),
        ("baz", "baz"),
        ("", ""),
    ],
)
def test_get_filename(path_, expected):
    """Testing get_filename."""
    assert processing.get_filename(path_) == expected


def test_get_file_data():
    """Testing get_file_data."""
    client_mock = MagicMock()
    client_mock.get_object.return_value.data = b"foo"
    assert processing.get_file_data(client_mock, "bucket", "bar/baz") == b"foo"
    client_mock.get_object.assert_called_once_with("bucket", "bar/baz")


def test_list_object_names():
    """Testing list_object_names."""
    client_mock = MagicMock()
    obj_name_1 = MagicMock(object_name="foo")
    obj_name_2 = MagicMock(object_name="bar")
    client_mock.list_objects.return_value = [obj_name_1, obj_name_2]
    res = processing.list_object_names(client_mock, "bucket", "path")
    assert res == ["foo", "bar"]


def test_get_pipeline_leaves_data():
    """Testing get_pipeline_leaves_data."""
    res = processing.get_pipeline_leaves_data(MagicMock(), "", "")
    assert res is not None


def test_get_pipeline_leaves_data_minio_error():
    """Testing get_pipeline_leaves_data when S3Error occurred."""
    err = S3Error("", "", "", "", "", "")
    with patch("src.result_processing.list_object_names", side_effect=err):
        res = processing.get_pipeline_leaves_data(MagicMock(), "", "")
        assert res is None


def test_merge_pipeline_leaves_data():
    """Testing merge_pipeline_leaves_data."""
    leaves_data = [
        b'{"pages": [{"page_num": 1, "size": {"width": 1, "height": 2}, '
        b'"objs": [{"id": 0, "bbox": [1, 1, 1, 1], "category": "some", '
        b'"data": {"a": 0}}]}]}',
        b'{"pages": [{"page_num": 1, "size": {"width": 1, "height": 2}, '
        b'"objs": [{"id": 0, "bbox": [1, 1, 1, 1], "category": "some", '
        b'"data": {"a": 1, "b": 2}}, '
        b'{"id": 3, "bbox": [3, 3, 3, 3], "category": "some"}]}]}',
    ]
    with patch(
        "src.result_processing.get_pipeline_leaves_data",
        return_value=leaves_data,
    ):
        res = processing.merge_pipeline_leaves_data(MagicMock(), "", "")
        expected = {
            "pages": [
                {
                    "page_num": 1,
                    "size": {"width": 1.0, "height": 2.0},
                    "objs": [
                        {
                            "id": 0,
                            "type": None,
                            "segmentation": None,
                            "bbox": (1.0, 1.0, 1.0, 1.0),
                            "links": None,
                            "category": "some",
                            "text": None,
                            "data": {"a": 1, "b": 2},
                            "children": None,
                            "tokens": None,
                            "confidence": None,
                        },
                        {
                            "id": 1,
                            "type": None,
                            "segmentation": None,
                            "bbox": (3.0, 3.0, 3.0, 3.0),
                            "links": None,
                            "category": "some",
                            "text": None,
                            "data": None,
                            "children": None,
                            "tokens": None,
                            "confidence": None,
                        },
                    ],
                }
            ]
        }
        assert res.dict() == expected


def test_merge_pipeline_leaves_data_no_files_data():
    """Testing merge_pipeline_leaves_data when there's no files data."""
    with patch(
        "src.result_processing.get_pipeline_leaves_data", return_value=None
    ):
        assert (
            processing.merge_pipeline_leaves_data(MagicMock(), "", "") is None
        )


def test_merge_pipeline_leaves_data_cannot_parse_data():
    """Testing merge_pipeline_leaves_data when raw data cannot be parsed."""
    with patch(
        "src.result_processing.ModelOutput.parse_models", return_value=None
    ):
        with patch("src.result_processing.get_pipeline_leaves_data"):
            assert (
                processing.merge_pipeline_leaves_data(MagicMock(), "", "")
                is None
            )


def test_merge_pipeline_leaves_data_cannot_merge_data():
    """Testing merge_pipeline_leaves_data when data cannot be merged."""
    with patch("src.result_processing.get_pipeline_leaves_data"):
        with patch("src.result_processing.ModelOutput.parse_models"):
            assert (
                processing.merge_pipeline_leaves_data(MagicMock(), "", "")
                is None
            )


def test_delete_objects():
    """Testing delete_objects."""
    with patch(
        "src.result_processing.list_object_names", return_value=["f", "b"]
    ):
        client_mock = MagicMock()
        assert processing.delete_objects(client_mock, "bucket", "")
        assert client_mock.remove_object.call_count == 2
        del_calls = client_mock.remove_object.call_args_list
        assert del_calls[0].args == ("bucket", "f")
        assert del_calls[1].args == ("bucket", "b")


def test_delete_objects_minio_error():
    """Testing delete_objects when S3Error occurred."""
    err = S3Error("", "", "", "", "", "")
    with patch("src.result_processing.list_object_names", side_effect=err):
        assert not processing.delete_objects(MagicMock(), "bucket", "")


def test_postprocess_result():
    """Testing postprocess_result."""
    m = MagicMock()
    m.content = b'{"foo": 42}'
    with patch(
        "src.result_processing.http_utils.make_request_with_retry",
        return_value=m,
    ) as req_mock:
        with patch(
            "src.result_processing.config.POSTPROCESSING_URI", "foo.com"
        ):
            res = processing.postprocess_result({"foo": 1})
            assert res == {"foo": 42}
            req_mock.assert_called_once_with(
                "foo.com", {"foo": 1}, method="POST", headers=None
            )


def test_postprocess_result_no_uri():
    """Testing postprocess_result when there's no uri."""
    with patch("src.result_processing.config.POSTPROCESSING_URI", ""):
        assert processing.postprocess_result({"a": 1}) is None


def test_postprocess_result_invalid_postprocessor_json_response():
    """Postprocessor return invalid json format."""
    m = MagicMock
    m.content = b'{"asd":}'
    with patch(
        "src.result_processing.http_utils.make_request_with_retry",
        return_value=m,
    ):
        assert processing.postprocess_result({"a": 1}) is None


def test_manage_result_for_annotator():
    """Testing manage_result_for_annotator."""
    with patch("src.result_processing.merge_pipeline_leaves_data"):
        with patch(
            "src.result_processing.postprocess_result",
            return_value={
                "file": "",
                "bucket": "",
                "input": {"pages": ["one", "two"]},
            },
        ):
            with patch(
                "src.result_processing.http_utils.make_request_with_retry"
            ) as req_mock:
                with patch("src.result_processing.delete_objects") as del_mock:
                    with patch("src.config.DEBUG_MERGE", False):
                        with patch(
                            "src.result_processing.config.ANNOTATION_URI",
                            "f.com/annotation",
                        ):
                            assert processing.manage_result_for_annotator(
                                "", "", "", 0, "", "", "", 1, MagicMock(), ""
                            )
                            req_mock.assert_called_once_with(
                                "f.com/annotation/annotation",
                                {"pipeline": 1, "pages": ["one", "two"]},
                                method="POST",
                                headers={
                                    "X-Current-Tenant": "",
                                    "Authorization": "Bearer ",
                                },
                            )
                            del_mock.assert_called_once()


def test_manage_result_for_annotator_no_annotator_uri():
    """Testing manage_result_for_annotator when there's no Annotator URI."""
    with patch("src.result_processing.config.ANNOTATION_URI", ""):
        assert not processing.manage_result_for_annotator(
            "", "", "", 0, "", "", "", 8, MagicMock(), ""
        )


def test_manage_result_for_annotator_cannot_merge_data():
    """Testing manage_result_for_annotator when data cannot be merger."""
    with patch(
        "src.result_processing.merge_pipeline_leaves_data", return_value=None
    ):
        assert not processing.manage_result_for_annotator(
            "", "", "", 0, "", "", "", 8, MagicMock(), ""
        )


def test_manage_result_for_annotator_request_not_succeeded():
    """Testing manage_result_for_annotator when cannot connect to Annotator."""
    with patch("src.result_processing.merge_pipeline_leaves_data"):
        with patch("src.result_processing.postprocess_result"):
            with patch(
                "src.result_processing.http_utils.make_request_with_retry",
                return_value=None,
            ):
                assert not processing.manage_result_for_annotator(
                    "", "", "", 0, "", "", "", 8, MagicMock(), ""
                )


def test_manage_result_for_annotator_request_debug_merge():
    """Debug merge is True and data are not deleted."""
    with patch("src.result_processing.merge_pipeline_leaves_data"):
        with patch("src.result_processing.postprocess_result"):
            with patch(
                "src.result_processing.http_utils.make_request_with_retry"
            ):
                with patch("src.result_processing.config.DEBUG_MERGE", True):
                    with patch(
                        "src.result_processing.delete_objects"
                    ) as del_mock:
                        assert processing.manage_result_for_annotator(
                            "", "", "", 0, "", "", "", 8, MagicMock(), ""
                        )
                        del_mock.assert_not_called()
