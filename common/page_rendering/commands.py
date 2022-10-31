import shutil
from pathlib import Path


def add_logger() -> None:
    current_path = Path(Path.cwd().parent) / "services" / "logger.py"
    install_path = Path.cwd() / "page_rendering-0.1.0" / "page_rendering"
    source_path = Path.cwd() / "page_rendering"
    shutil.copy(str(current_path), str(source_path))
    shutil.copy(str(current_path), str(install_path))


def get_setup() -> None:
    current_path = Path.cwd() / "page_rendering-0.1.0" / "setup.py"
    source_path = Path.cwd()
    shutil.move(str(current_path), str(source_path))
