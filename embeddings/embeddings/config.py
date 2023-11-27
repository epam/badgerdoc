from dotenv import find_dotenv
from pydantic import BaseSettings


class Settings(BaseSettings):
    app_title: str
    root_path: str = ""

    class Config:
        env_file: str = find_dotenv(".env")
        env_file_encoding = "utf-8"


settings = Settings()
