from typing import Optional
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture
from fastapi import FastAPI

from badgerdoc_cli import main


def test_init_cli_app() -> None:
    app = FastAPI()
    main.init_cli_app(app)
    assert main.APP is app


def test_init_cli_app_invalid_app() -> None:
    fake_app = type("FastAPI", (), {})
    with pytest.raises(TypeError, match="Invalid app type. Must be FastAPI"):
        main.init_cli_app(fake_app)


def test_verbose_param() -> None:
    with patch(
        "badgerdoc_cli.main.generate_openapi",
        side_effect=ValueError("Foo!"),
    ), pytest.raises(ValueError, match="Foo"):
        app = FastAPI()
        cli_args = ("--verbose", "openapi", "foo.json")
        main.init_cli_handlers(app, cli_args)


@pytest.mark.parametrize(("indent", "expected_indent"), ((None, 2), ("4", 4)))
def test_openapi_command(indent: Optional[str], expected_indent: int) -> None:
    app = FastAPI()
    cli_args = ["openapi", "foo.json"]
    if indent is not None:
        cli_args.append(f"--indent={indent}")

    with patch("badgerdoc_cli.main.generate_openapi") as gendoc_mock:
        main.init_cli_handlers(app, cli_args)
    gendoc_mock.assert_called_once_with(
        app=app,
        file_path="foo.json",
        indent=expected_indent,
    )


def test_openapi_command_non_initialized_cli(
    capsys: CaptureFixture[str],
) -> None:
    app = None
    cli_args = ("openapi", "foo.json")
    main.init_cli_handlers(app, cli_args)
    captured_stdout = capsys.readouterr().out
    expected = "CLI is not initialized. Add init_cli_app call to set up CLI\n"
    assert captured_stdout == expected


def test_openapi_command_invalid_file_format(
    capsys: CaptureFixture[str],
) -> None:
    app = FastAPI()
    cli_args = ("openapi", "foo.pdf")
    main.init_cli_handlers(app, cli_args)
    captured_stdout = capsys.readouterr().out
    expected = "Invalid file format. Must be .json\n"
    assert captured_stdout == expected
