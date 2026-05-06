black:
	uv run black web workflows

isort:
	uv run isort web workflows

mypy:
	uv run mypy web workflows --check-untyped-defs

pylint:
	uv run pylint web workflows --exit-zero

bandit:
	uv run bandit -r web workflows --exclude venv,tests

quality_gate:
	set +e; \
	$(MAKE) black; \
	$(MAKE) isort; \
	$(MAKE) mypy; \
	$(MAKE) pylint; \
	$(MAKE) bandit; \
	set -e

test:
	docker compose exec web uv run python manage.py test

test_specific:
	docker compose exec web uv run python manage.py test $(TEST)

build_frontend:
	cd web/frontend && npm install
	cd web/frontend && npm run build

build_base:
	docker build -f workflows/Dockerfile.base -t badgerdoc-workflows-base workflows/

build_all:
	$(MAKE) build_frontend
	$(MAKE) build_base

stop_mlx:
	-lsof -ti:11434 | xargs kill -9 2>/dev/null || true
	-lsof -ti:11435 | xargs kill -9 2>/dev/null || true
	-lsof -ti:11436 | xargs kill -9 2>/dev/null || true

start_mlx: stop_mlx
	uv run mlx_vlm.server --port 11434 --model mlx-community/DeepSeek-OCR-2-bf16 & \
	uv run mlx_vlm.server --port 11435 --model mlx-community/PaddleOCR-VL-1.5-bf16 & \
	uv run mlx_vlm.server --port 11436 --model mlx-community/MinerU2.5-2509-1.2B-bf16
