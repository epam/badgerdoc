import shutil
from pathlib import Path


def add_logger() -> None:
    current_path = Path(Path.cwd().parent) / "services" / "logger.py"

    source_path = Path.cwd() / "minio_service"
    install_path = Path.cwd() / "minio-service-0.1.0" / "minio_service"
    shutil.copy(str(current_path), str(source_path))
    shutil.copy(str(current_path), str(install_path))


def get_setup() -> None:
    current_path = Path.cwd() / "minio-service-0.1.0" / "setup.py"
    source_path = Path.cwd()
    shutil.move(str(current_path), str(source_path))
