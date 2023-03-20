import requests
from assets import logger
from assets.config import settings

LOGGER = logger.get_logger(__name__)


class UploadError(Exception):
    """
    Raises when file was not uploaded
    """


def post_txt_to_convert(
    bucket: str, input_text, output_pdf, output_tokens
) -> None:
    """
    Puts txt file into convert service
    """
    try:
        response = requests.post(
            url=settings.service_convert_txt,
            json={
                "input_text": {"bucket": bucket, "path": input_text},
                "output_pdf": {"bucket": bucket, "path": output_pdf},
                "output_tokens": {"bucket": bucket, "path": output_tokens},
            },
        )
        if response.status_code != 201:
            raise UploadError(
                "File %s failed to convert: %s", input_text, response.text
            )
    except requests.exceptions.ConnectionError as e:
        LOGGER.error(f"Connection error - detail: {e}")
    LOGGER.info(f"File {input_text} successfully converted")


def post_pdf_to_convert(bucket: str, input_pdf, output_tokens) -> None:
    """
    Puts pdf from html file into convert service
    """
    try:
        response = requests.post(
            url=settings.service_convert_pdf,
            json={
                "input_pdf": {"bucket": bucket, "path": input_pdf},
                "output_tokens": {"bucket": bucket, "path": output_tokens},
            },
        )
        if response.status_code != 201:
            raise UploadError(
                "File %s failed to convert: %s", input_pdf, response.text
            )
    except requests.exceptions.ConnectionError as e:
        LOGGER.error("Connection error - detail: %s", e)
    LOGGER.info("File %s successfully converted", {input_pdf})
