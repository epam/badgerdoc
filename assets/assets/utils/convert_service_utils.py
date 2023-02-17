import requests
from assets import logger
from assets.config import settings

logger_ = logger.get_logger(__name__)


def post_to_convert(
    bucket: str, input_text, output_pdf, output_tokens
) -> bool:
    """
    Puts file into convert service
    """
    try:
        response = requests.post(
            url=settings.service_convert_uri,
            json={
                "input_text": {"bucket": bucket, "path": input_text},
                "output_pdf": {"bucket": bucket, "path": output_pdf},
                "output_tokens": {"bucket": bucket, "path": output_tokens},
            },
        )
        if response.status_code != 201:
            logger_.info(
                f"File {input_text} failed to convert: " f"{response.text}"
            )
            return False
    except requests.exceptions.ConnectionError as e:
        logger_.error(f"Connection error - detail: {e}")
        return False
    logger_.info(f"File {input_text} successfully converted")
    return True
