import argparse
import code
import json
import sys
from typing import Any, Dict, Protocol

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


class SupportsAddParser(Protocol):
    def add_parser(
        self, name: str, **kwargs: Dict[str, Any]
    ) -> argparse.ArgumentParser:
        pass


def shell_run() -> None:
    code.interact()


def inject_shell_commands(subparsers: SupportsAddParser) -> None:
    shell_parser = subparsers.add_parser("shell")
    shell_parser.set_defaults(func=shell_run)


def generate_openapi(app: FastAPI, path: str, indent: int = 2) -> None:
    with open(path, "w") as f_o:
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
    app: FastAPI, subparsers: SupportsAddParser
) -> None:
    def save_openapi(arguments: Dict[str, Any]) -> None:
        generate_openapi(
            app=app, path=arguments["path"], indent=arguments["indent"]
        )

    openapi_parser = subparsers.add_parser("openapi")
    openapi_parser.add_argument("path", help="path to save spec to")
    openapi_parser.add_argument(
        "--indent", help="indents in json open api spec", default=2
    )
    openapi_parser.set_defaults(func_with_args=save_openapi, app=app)


def init_cli_handlers(app: FastAPI, arguments: Any) -> None:
    parser = argparse.ArgumentParser("pipelines")
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
            print("--help for available commands")
    except AttributeError:
        parser.print_help()


if __name__ == "__main__":
    from pipelines import app

    init_cli_handlers(app, sys.argv[1:])
