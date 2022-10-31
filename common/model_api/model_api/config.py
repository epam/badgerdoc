from pydantic import BaseSettings


# todo: optimize settings
class Settings(BaseSettings):
    """Settings.
    Some of these settings are overridden by environment variables"""

    # log_file: str = "./log.log"
    volume_path: str = "/volume"  # exclude
    model_path: str = "model"  # exclude
    verbose_feature: bool = True  # exclude
    training_dpi: int = 224
    training_image_format: str = "png"
    app_host: str = "0.0.0.0"  # exclude
    app_port: int = 8000  # exclude
    root_path: str = ""  # exclude
    request_prefix = "/v1/models"  # how to use in main app
    minio_host: str = "minio:9000"  # how to use in main app
    minio_access_key: str = "minio"  # how to use in main app
    minio_secret_key: str = "minio123"  # how to use in main app
    data_bucket: str = "annotation"  # exclude
    data_file: str = "export.pkl"  # exclude
    config_bucket: str = "annotation"  # exclude
    config_file: str = ""  # exclude
    model_name: str = "export"  # how to use in main app
    device: str = "cpu"  # exclude


settings = Settings()
