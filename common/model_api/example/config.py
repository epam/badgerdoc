from pydantic import BaseSettings


# todo: optimize settings
class Settings(BaseSettings):
    """Settings.
    Some of these settings are overridden by environment variables"""

    # log_file: str = "./log.log"
    volume_path: str = "/volume"
    model_path: str = "model"
    verbose_feature: bool = True
    training_dpi: int = 224
    training_image_format: str = "png"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    root_path: str = ""
    request_prefix = "/v1/models"
    minio_host: str = "minio:9000"
    minio_access_key: str = "minio"
    minio_secret_key: str = "minio123"
    data_bucket: str = "annotation"
    data_file: str = "export.pkl"
    config_bucket: str = "annotation"
    config_file: str = ""
    model_name: str = "export"
    device: str = "cpu"


settings = Settings()
