# Badgerdoc 2

Badgerdoc is a human-in-the-loop tool designed for working with documents that have been analyzed by AI. It provides a platform for users to review, validate, and interact with the output of various AI tools, including OCR, table and chart extractions, and more.

# Contributing

## Before you start

We're following next rules in this repository:

- We follow https://12factor.net/.
- We follow https://google.github.io/styleguide/pyguide.html.
- We follow PEP8.
- We use AI-generated code, but we clearly understand what this code does.
- We do not write bash scripts unless they are necessary for infrastructure setup.
- We maintain a clear project structure. In most cases, classes have their own modules; functions are preferred.
- We comment code only when necessary to explain complex logic.
- We keep all dependencies at the package level and understand every dependency and its purpose. If we add a dependency, we can clearly explain what it does.
- We write unit tests.
- We do not change the project structure without agreement from the Solution Architect or Tech Leads.
- We use asynchronous packages whenever possible except for Django part. Django is synchronous.
- We write optimized code with a focus on performance.
- We write package README.md files with the help of AI, but we do not generate them entirely using AI. We include only valuable information in the README.
- We all agree that both clean code and development speed matter.
- Before contributing, I agree to the rules above.

## Project Structure

### Web
Web is a Django project with the Badgerdoc 2 application installed. Every model and view has its own module. Every class has its own module.

### Workflows
`workflows/` is a collection of Temporal workflows and workers. Every worker has its own package and a list of workflows. All workflow code is separated into activities. Workflows do not share any code with other workflows. Common code is located in the `badgerdoc_common` package.

We follow the following naming conventions:
- The `badgerdoc_` prefix is used for core workflows or core functionality.

We follow these principles when writing Temporal code:
- We build workflows as reusable components, adhering to the Single Responsibility Principle.
- We avoid writing code inside workflows; instead, we use activities for all code.
- We call sub-workflows using their WorkflowType by name, not by class.
- The `task_queue` always has the same name as the package.

### Storage
We use S3 for storing files; for local installations, we use MinIO. Every workflow uses its own folder (not bucket, but folder) for storing files. There are two types of files: temporary and permanent. Temporary files must be stored in a folder built using the pattern: `tmp/workflows/<package_name>/<workflow_type>/<workflow_id>/`. Permanent files must be stored in a folder built using the pattern: `data/workflows/<package_name>/<workflow_type>/<workflow_id>/`.


# Development

## Prerequisites

- Docker and Docker Compose installed

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd badgerdoc-2
```

2. Configure environment variables:
```bash
cp .env_example .env
```

3. Start all services:
```bash
make build_all
docker compose up --build
```

4. Access the application:
- Web application: http://localhost:80/
- Temporal UI: http://localhost:8080/
- Minio UI: http://localhost:9001/


### Post-Setup Configuration

After the first run:

1. Create a superuser:
```bash
docker compose exec web uv run python manage.py createsuperuser
```

2. Generate token for the superuser:
```bash
docker compose exec web uv run python manage.py drf_create_token admin
```

3. Put the token in the `.env` file:
```bash
BADGERDOC_TOKEN=<token>
```

4. Navigate to `http://localhost:9001/`, login with `minioadmin`, create a bucket named `badgerdoc` to enable upload of the documents.

## Swagger

Web application supports all actions by RestAPI. To simplify development and experimentation, use Swagger UI available at http://localhost:80/swagger/

### Authentication

Swagger supports Basic Authentication (use username and password) in Basic Authorization form. However, for using RestAPI Badgerdoc in server-to-server communication, strongly recommend using token authentication. In previous steps you generated token, this token can be used for authentication. Header `Authorization: token <token>` should be enough to authorize requests.

## MLX on MacOS

MLX (Apple Silicon Machine Learning Framework) is available on MacOS for running VLM (Vision Language Model) inference locally. This project uses MLX-VLM to run OCR models like DeepSeek-OCR-2 and PaddleOCR-VL.

> **Note:** MinIO runs inside Docker and is referenced by the hostname `minio` in pre-signed URLs returned by the API. When using MLX locally, the host machine must be able to resolve that hostname. Add the following entry to `/etc/hosts`:
>
> ```
> 127.0.0.1 minio
> ```

### Installation

Install the MLX dependency group using uv:

```bash
uv sync --group mlx
```

Or install it along with dev dependencies:

```bash
uv sync --group dev --group mlx
```

### Starting MLX VLM Servers

After installation, start the MLX VLM servers using:

```bash
make start_mlx
```

This will start two VLM servers:
- **Port 11434**: DeepSeek-OCR-2-bf16
- **Port 11435**: PaddleOCR-VL-1.5-bf16

Stop the servers using **Ctrl+C**.
