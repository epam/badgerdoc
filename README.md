# Badgerdoc 2

Badgerdoc is a human-in-the-loop tool designed for working with documents that have been analyzed by AI. It provides a platform for users to review, validate, and interact with the output of various AI tools, including OCR, table and chart extractions, and more.


# How to install Badgerdoc

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


## Post-Setup Configuration

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

# How to Contribute

Setting up Badgerdoc locally (see [How to install Badgerdoc](#how-to-install-badgerdoc) above) is a mandatory part of contribution. Once the application is running, the contribution guidelines are available at [How to Contribute](http://127.0.0.1/docs/how_to_contribute/).

## How to Make Pull Request

1. Carefully read the [How to Contribute](#how-to-contribute) documentation.
2. Create a fork of the Badgerdoc GitHub repository.
3. Make all your changes in your own fork.
4. Create a Pull Request to the Badgerdoc repository targeting the `main` branch.
5. Squash your changes into a single commit before submitting — PRs must contain exactly 1 commit.
6. One of the core developers will review the PR, approve it, and merge it.
