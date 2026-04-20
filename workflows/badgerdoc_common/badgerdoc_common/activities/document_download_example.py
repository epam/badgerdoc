import logging
import tempfile
from io import BytesIO
from pathlib import Path

from badgerdoc_common.activities.document import badgerdoc_get_document
from badgerdoc_common.badgerdoc_http import badgerdoc_download

logger = logging.getLogger(__name__)


async def example_with_named_temporary_file(document_id: int) -> str:
    document = await badgerdoc_get_document(document_id)

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{document.extension}"
    ) as temp_file:
        buffer = BytesIO()
        await badgerdoc_download(buffer, document)
        temp_file.write(buffer.read())
        temp_file_path = temp_file.name

    logger.info("Document downloaded to: %s", temp_file_path)
    return temp_file_path


async def example_with_temporary_directory(document_id: int) -> Path:
    document = await badgerdoc_get_document(document_id)

    with tempfile.TemporaryDirectory() as temp_dir:
        buffer = BytesIO()
        await badgerdoc_download(buffer, document)
        file_path = Path(temp_dir) / f"{document.name}.{document.extension}"
        with open(file_path, "wb") as f:
            f.write(buffer.read())

        logger.info("Document downloaded to: %s", file_path)
        return file_path


async def example_with_bytesio_only(document_id: int) -> BytesIO:
    document = await badgerdoc_get_document(document_id)

    buffer = BytesIO()
    await badgerdoc_download(buffer, document)

    logger.info(
        "Document downloaded to buffer. Size: %d bytes", len(buffer.getvalue())
    )
    return buffer
