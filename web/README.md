# Badgerdoc Web Application

This directory contains the main Django web application for the Badgerdoc project.

## Documentation Development

The project documentation is built using MkDocs and is located in the root `docs/` directory.

### Installation

To work on the documentation, you must first sync the dependencies from the lock file. From this `web/` directory, run:

```sh
uv sync --extra docs
```

If the `uv.lock` file is missing or out of date, you may need to regenerate it first:

```sh
uv lock --extra docs
```

### Local Development Server

To serve the documentation locally and see your changes live, run the following command from this `web/` directory:

```sh
uv run mkdocs serve -f ../docs/mkdocs.yml
```

This will start a local development server, and you can view the documentation in your browser at the address provided (usually `http://127.0.0.1:8000`).
