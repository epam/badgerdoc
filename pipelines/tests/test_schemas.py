"""Testing pipelines/schemas.py."""

import pytest
import tests.testing_data as td

import pipelines.db.models as dbm
import pipelines.schemas as schemas


def test_init_input_args():
    """Testing __init__ of InputArguments."""
    args = td.input_args_1
    assert args._current_step_id == "baz"
    assert args._path == "qwe/foo/bar"
    assert args._labels == ["a", "b"]
    assert args._is_init


def test_next_step_args_inference():
    """Testing next_step_args of InputArguments."""
    args = td.input_args_1
    res = args.next_step_args(schemas.PipelineTypes.INFERENCE, "zxc", {"c": 3})
    assert res.input == {"c": 3}
    assert res.input_path == args.output_path
    assert res.output_path == args._path + "/zxc.json"
    assert not res._is_init


def test_next_step_args_preprocessing():
    """Testing next_step_args of InputArguments."""
    args = td.input_args_1
    res = args.next_step_args(
        schemas.PipelineTypes.PREPROCESSING, "zxc", {"c": 3}
    )
    assert res.input == {"c": 3}
    assert res.input_path == args.output_path
    assert res.output_path == args.output_path
    assert not res._is_init


def test_prepare_for_init_inference():
    """Testing prepare_for_init of InputArguments."""
    res = td.input_args_1.prepare_for_init(
        schemas.PipelineTypes.INFERENCE, "baz"
    )
    d = td.input_args_1.dict()
    d.update({"input_path": td.input_args_1.output_path})
    expected = {
        **d,
        "output_path": td.input_args_1.output_path + "/baz.json",
    }
    assert res.dict() == expected


def test_prepare_for_init_preprocessing():
    """Testing prepare_for_init of InputArguments."""
    res = td.input_args_1.prepare_for_init(
        schemas.PipelineTypes.PREPROCESSING, "baz"
    )
    d = td.input_args_1.dict()
    d.update({"input_path": td.input_args_1.output_path})
    expected = {
        **d,
        "output_path": td.input_args_1.output_path,
    }
    assert res.dict() == expected


def test_append_path():
    """Testing append_path of InputArguments."""
    assert td.input_args_1.append_path("bar") == "qwe/foo/bar/bar"


@pytest.mark.parametrize(
    ["path", "expected"], [("asd/qwe/wsx", "wsx"), ("asd/qwe/wsx/", "wsx")]
)
def test_get_step_id_from_path(path, expected):
    """Testing get_step_id_from_path of InputArguments."""
    assert td.input_args_1.get_step_id_from_path(path) == expected


def test_get_path():
    """Testing get_path of InputArguments."""
    assert td.input_args_1.get_path() == "qwe/foo/bar"


def test_get_path_dont_trim():
    """Testing get_path of InputArguments without trimming last path component."""
    assert td.input_args_1.get_path(trim=False) == "qwe/foo/bar/baz"


def test_get_output_bucket():
    """Testing get_output_bucket of InputArguments."""
    assert td.input_args_1.get_output_bucket() == ""
    assert td.input_args_2.get_output_bucket() == "output_bucket"


def test_get_filename():
    """Testing get_filename of InputArguments."""
    assert td.input_args_1.get_filename() == "fileId"


@pytest.mark.parametrize(
    ["input_", "is_init"], [(None, True), (None, False), ({"a": 1}, True)]
)
def test_create_input_by_label_no_input_or_just_init(input_, is_init):
    """Testing create_input_by_label of InputArguments when there's no input."""
    args = td.input_args_1.copy(update={"input": input_, "_is_init": is_init})
    res = args.create_input_by_label(None)
    assert res == args
    assert res is not args


def test_create_input_by_label():
    """Testing create_input_by_label of InputArguments."""
    args = td.input_args_1.copy()
    args._is_init = False
    args = args.create_input_by_label("a")
    assert args.input == {"a": {"aa": 1}}
    assert args is not td.input_args_1


def test_create_input_by_label_universal_label():
    """Testing create_input_by_label of InputArguments when there's no label
    and universal label is taken."""
    args = td.input_args_1.copy(update={"input": {"result": {"res": 42}}})
    args._is_init = False
    args = args.create_input_by_label(None)
    assert args.input == {"result": {"res": 42}}
    assert args is not td.input_args_1


def test_create_input_by_label_no_input_by_label():
    """Testing create_input_by_label of InputArguments when there's no such
    label in the input."""
    args = td.input_args_1.copy()
    args._is_init = False
    args = args.create_input_by_label(None)
    assert args.input == td.input_args_1.input


@pytest.mark.parametrize(
    ["entity", "expected_value"],
    [
        (dbm.Pipeline(), "Pipeline"),
        (dbm.PipelineExecutionTask(), "PipelineExecutionTask"),
        (dbm.ExecutionStep(), "ExecutionStep"),
        (dbm.ExecutorHeartbeat(), "ExecutorHeartbeat"),
    ],
)
def test_entity_type(entity: dbm.Table, expected_value: str):
    """Testing entity_type of Entity."""
    assert schemas.Entity.entity_type(entity) == expected_value


def test_invalid_entity():
    """Testing entity_type of Entity when there's no such entity in Enum."""
    with pytest.raises(ValueError):
        schemas.Entity.entity_type(dbm.MainEventLog())


@pytest.mark.parametrize(
    ("data", "args", "result"),
    [
        (
            td.exec_input_args,
            ["file", "bucket"],
            {"file": "foo/bar/baz.gz", "bucket": "buck-et"},
        ),
        (td.exec_input_args, [], {}),
        (
            td.exec_input_args,
            ["file", "bucket", "output_path", "pages"],
            td.exec_input_args,
        ),
    ],
)
def test_filter_dict_by_categories(data, args, result):
    assert (
        schemas.InputArguments.filter_dict_by_categories(data, args) == result
    )
