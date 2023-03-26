import argparse
import code
import json
import sys
from typing import Any, Dict, Optional, Protocol

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

APP = None


class SupportsAddParser(Protocol):
    def add_parser(self, name: str, **kwargs: str) -> argparse.ArgumentParser:
        pass


def shell_run() -> None:
    code.interact()


def inject_shell_commands(subparsers: SupportsAddParser) -> None:
    shell_parser = subparsers.add_parser("shell")
    shell_parser.set_defaults(func=shell_run)


def generate_openapi(app: FastAPI, file_path: str, indent: int = 2) -> None:
    with open(file_path, "w") as f_o:
        json.dump(
            get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
                tags=app.openapi_tags,
            ),
            f_o,
            indent=indent,
        )
        f_o.write("\n")


def inject_openapi_commands(
    app: Optional[FastAPI], subparsers: SupportsAddParser
) -> None:
    def _generate_openapi(arguments: Dict[str, Any]) -> None:
        path: str = arguments["path"]
        if not path.endswith(".json"):
            raise ValueError("Invalid file format. Must be .json")
        if app is None:
            raise ValueError(
                "CLI is not initialized. Add init_cli_app call to set up CLI"
            )
        generate_openapi(app=app, file_path=path, indent=arguments["indent"])

    openapi_parser = subparsers.add_parser(
        "openapi", help="generate openapi specification"
    )
    openapi_parser.add_argument("path", help="path to save spec to")
    openapi_parser.add_argument(
        "--indent", help="indents in json open api spec", default=2
    )
    openapi_parser.set_defaults(func_with_args=_generate_openapi)


def init_cli_handlers(app: Optional[FastAPI], arguments: Any) -> None:
    parser = argparse.ArgumentParser("badgerdoc")
    parser.add_argument(
        "-v",
        "--verbose",
        help="show full traceback and other debug info",
        action="store_true",
    )
    subparsers = parser.add_subparsers()
    inject_openapi_commands(app, subparsers)
    params = vars(parser.parse_args(arguments))
    try:
        if params.get("func"):
            params["func"]()
        elif params.get("func_with_args"):
            params["func_with_args"](
                {
                    param: value
                    for param, value in params.items()
                    if param not in {"func", "func_with_args"}
                }
            )
        else:
            parser.print_help()
    except AttributeError:
        parser.print_help()
    except Exception as err:
        if params.get("verbose"):
            raise
        print(err)


def init_cli_app(app: FastAPI) -> None:
    if not isinstance(app, FastAPI):
        raise TypeError("Invalid app type. Must be FastAPI")
    global APP
    APP = app


def cli_handler():
    init_cli_handlers(APP, sys.argv[1:])
