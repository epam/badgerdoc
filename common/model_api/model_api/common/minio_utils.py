from minio import Minio

from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)


class MinioCommunicator:
    client: Minio = None

    def __init__(self) -> None:
        if not self.client:
            self.create_client()

    @classmethod
    def create_client(cls) -> None:
        cls.client = Minio(
            endpoint=settings.minio_host,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        logger.info(
            "MinIO client for %s was created successfully. Buckets: %s",
            settings.minio_host,
            cls.client.list_buckets(),
        )
