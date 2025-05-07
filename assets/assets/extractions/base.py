import abc
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Optional

from badgerdoc_storage import storage as bd_storage

import assets.db.service
from assets.db.models import FileObject, FilesExtractions

logger = logging.getLogger(__name__)

ASSETS_EXTRACTOR_SIGNED_URL_TTL = os.environ.get(
    "ASSETS_EXTRACTOR_SIGNED_URL_TTL", 60
)


class Extraction(abc.ABC):
    """
    Abstract base class for all extraction engines.
    """

    def __init__(self, session: Any, tenant: str) -> None:
        self.extraction: Optional[FilesExtractions] = None
        self.session = session
        self.tenant = tenant

    @property
    @abc.abstractmethod
    def enabled(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def engine(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def file_extension(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def file_content_type(self) -> str:
        pass

    @abc.abstractmethod
    def calculate_page_count(self) -> int:
        pass

    @abc.abstractmethod
    async def extract(self, file: FileObject) -> None:
        pass

    async def gen_signed_url(self, file: FileObject) -> str:
        """
        Get a signed URL for the file from storage.
        This should replace the hardcoded URL in the original code.
        """
        # Assuming bd_storage.get_storage(self.tenant)
        # is a valid method to get storage
        logger.debug("Generating signed URL for file %s", file.id)
        return bd_storage.get_storage(self.tenant).gen_signed_url(
            file.path, ASSETS_EXTRACTOR_SIGNED_URL_TTL
        )

    async def start(self, file: FileObject) -> bool:
        if not self.enabled:
            return False
        logger.debug("Starting extraction for file %s", file.id)
        unique_id = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = f"files/{file.id}/extractions/{self.engine}/{unique_id}"
        page_count = self.calculate_page_count()
        self.extraction = assets.db.service.create_extraction(
            session=self.session,
            file_id=file.id,
            engine=self.engine,
            file_path=file_path,
            page_count=page_count,
            file_extension=self.file_extension,
        )
        return True

    async def store(self, page_num: int, data: Any) -> None:
        logger.debug(
            "Storing page %s data for file %s",
            page_num,
            self.extraction.file_id,
        )
        if not self.extraction:
            raise ValueError(
                "Extraction not initialized. Call extract() first."
            )

        page_file_path = (
            f"{self.extraction.file_path}/{page_num}.{self.file_extension}"
        )

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(data)
            temp_file.flush()  # Ensure all data is written
            temp_file.seek(0)  # Rewind to beginning of file
            try:
                bd_storage.get_storage(self.tenant).upload(
                    page_file_path,
                    temp_file_path,
                    content_type=self.file_content_type,
                )
            except Exception:
                logger.exception("Failed to upload file to storage")
                raise

    async def finish(self) -> None:
        logger.debug(
            "Finishing extraction for file %s", self.extraction.file_id
        )
        assets.db.service.finish_extraction(self.session, self.extraction)
        self.extraction = None
