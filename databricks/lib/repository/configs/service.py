from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict

import yaml


def get_config_file_path() -> Path:

    parent_path = Path.cwd().parent

    while parent_path != parent_path.parent:
        config_path = parent_path / "config.yaml"
        if config_path.exists():
            return config_path
        parent_path = parent_path.parent

    raise FileNotFoundError("Config file not found.")


def load_config(project_name: str) -> Dict[str, Any]:

    with open(get_config_file_path(), "r") as file:
        config: Dict[str, Dict[str, Any]] = yaml.safe_load(file)

        # Get the config for the specified project and environment
        project_config = config.get(project_name, {})
        if not project_config:
            raise ValueError(
                f"Configuration for project '{project_name}' not found."
            )

        return project_config


def write_config(config: ConfigParser, env: str) -> None:
    pass
