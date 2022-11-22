from minio import Minio

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__file__)


class MinioCommunicator:
    client: Minio = None

    def __init__(self) -> None:
        if not MinioCommunicator.client:
            self.create_client()

    @classmethod
    def create_client(cls) -> None:
        cls.client = Minio(
            endpoint=settings.minio_server,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            secure=False,
        )
        logger.info(
            "MinIO client for %s was created successfully",
            settings.minio_server,
        )
