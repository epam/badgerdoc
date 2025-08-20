import yaml
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

ROOT = Path(__file__).parent
DEFAULTS_PATH = ROOT / "config" / "defaults.yaml"


class Settings(BaseSettings):
    BASE_URL: str
    API_USER: str
    API_PASS: SecretStr
    TIMEOUT_SECONDS: int = 30
    MAX_WORKERS: int = 4
    USE_MOCK_LLM: bool = True
    LOG_LEVEL: str = "INFO"
    LLM_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def load_settings() -> Settings:
    with open(DEFAULTS_PATH, "r") as f:
        yaml_defaults = yaml.safe_load(f)

    from dotenv import dotenv_values

    env_data = dotenv_values(".env")

    merged = {
        **yaml_defaults,
        **{k: v for k, v in env_data.items() if v is not None},
    }

    return Settings(**merged)
