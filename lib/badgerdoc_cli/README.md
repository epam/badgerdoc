<p style="font-size: 15vw; text-align: center">
    <span style="color: #3f8dc8">Badgerdoc CLI</span>
</p>
<p style="text-align: center">
    <em>Badgerdoc CLI simplify routine actions for the project, simple and ready to go</em>
</p>

---
## Requirements
[Python 3.8+ ](https://www.python.org/downloads/)
## Installation
### Install to local environment
- Clone repository `git clone git@github.com:epam/badgerdoc.git`
- Change directory `cd badgerdoc/lib/badgerdoc_cli`
- Create and activate virtualenv `python3.8 -m venv venv` and `source venv/bin/activate`
- Install CLI tool `pip install .`
- Install development dependencies if needed `pip install ."[dev]"`
### Integrate to service
- Add library to service dependencies and install (see [Install to local environment](#install-to-local-environment))
- Add cli handler for the service to the main module with `FastAPI`
```python
from fastapi import FastAPI
from some_module import another_router

app = FastAPI(
    title="sample app",
    description="very important service",
)
app.include_router(another_router)

def cli_handler() -> None:
    from badgerdoc_cli import cli_handler, init_cli_app

    init_cli_app(app)
    cli_handler()
```
NOTICE! Add cli handler at the end of the module after all routers are initialized. <br>
You can use `cli_handler` from the box without initializing `FastAPI` app, you will simply have less functionality
```python
def cli_handler() -> None:
    from badgerdoc_cli import cli_handler
    cli_handler()
```
- [Poetry] Add cli handler entry point to your `pyproject.toml`
```toml
[tool.poetry.scripts]
badgerdoc = "some_package.some_module:cli_handler"
```
- Now you can use CLI tool using `badgerdoc` command
---
## Usage
```shell
$ badgerdoc
usage: badgerdoc [-h] [-v] {openapi} ...

positional arguments:
  {openapi}
    openapi      generate openapi specification

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  show full traceback and other debug info (default: False)
```
### badgerdoc openapi
```shell
$ badgerdoc openapi
usage: badgerdoc openapi [-h] [--indent INDENT] path

positional arguments:
  path             path to save spec to

optional arguments:
  -h, --help       show this help message and exit
  --indent INDENT  indents in json open api spec (default: 2)
```
Example:
```shell
$ badgerdoc openapi example.json
Documentation is saved at /Users/badgerdoc/projects/badgerdoc/annotation/example.json
$ cat example.json
{
  "openapi": "3.0.2",
  "info": {
    "title": "Badgerdoc Annotation",
    "version": "0.1.5"
  },
  "paths": {
    "/annotation/{task_id}": {
      "post": {
        "tags": [
          "Annotation"
        ],
    ...
```
