import logging
from typing import Literal

from badgerdoc_storage import storage as bd_storage

from jobs import config

logger = logging.getLogger(__name__)


class NotConfiguredException(Exception):
    pass


def create_pre_signed_s3_url(
    bucket: str,
    path: str,
    action: Literal["get_object"] = "get_object",
    expire_in_hours: int = config.JOBS_SIGNED_URL_TTL,
) -> str:
    return bd_storage.get_storage(bucket).gen_signed_url(path, expire_in_hours)
