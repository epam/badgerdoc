import requests
from badgerdoc_storage import storage as bd_storage

from assets import logger
from assets.config import settings
from assets.utils.convert.pdf import PDFToBadgerdocConverter

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


def post_pdf_to_convert(tenant: str, input_pdf, output_tokens) -> None:
    """
    TODO: rename this function
    Puts pdf from html file into convert service
    """
    LOGGER.debug(
        "Converting file: %s, into output_tokens: %s", input_pdf, output_tokens
    )
    pdf_converter = PDFToBadgerdocConverter(bd_storage.get_storage(tenant))
    pdf_converter.execute(
        s3_input_pdf=input_pdf,
        s3_output_tokens=output_tokens,
    )
