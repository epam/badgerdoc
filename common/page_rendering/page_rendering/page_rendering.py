from pathlib import Path
from typing import List, Optional

import pdfplumber
from minio_service.minio_api import MinioCommunicator

from .logger import get_logger

logger = get_logger(__name__, "PAGE_RENDERING_PATH", "page_rendering")


class RenderImages:
    """
    Render image pages and save to local file
    """

    def __init__(self, file_name: str, dpi: int, image_format: str) -> None:
        self.file_name = file_name
        self.dpi = dpi
        self.image_format = image_format

    def render(
        self,
        pages: List[int],
        dir_with_images: Optional[Path] = Path("Images"),
        file_path: Optional[Path] = None,
    ) -> None:
        """
        Render local file pages
        Args:
            pages: pages list of the image
            file_path: local path to file
            dir_with_images: Folder for images saving
        """
        full_file_name = file_path if file_path else Path(self.file_name)

        if not pages or any(page <= 0 for page in pages):
            logger.error("Pages should be positive integer values")
            raise ValueError("Pages should be positive integer values")
        with pdfplumber.open(full_file_name) as pdf:
            if not dir_with_images.exists():
                Path.mkdir(dir_with_images, parents=True, exist_ok=True)
            for page_number in pages:
                page = pdf.pages[page_number - 1]
                img = page.to_image(resolution=self.dpi)
                file_name = full_file_name.name.split(".")[0]
                filename = dir_with_images / self.name_image(
                    file_name, page_number
                )
                logger.info("Render page %s", page_number)
                img.save(filename, format=self.image_format)

    def render_from_minio(
        self,
        pages: List[int],
        bucket: str,
        minio_path: Path,
        local_path: Optional[Path] = Path("Files"),
    ) -> None:
        """
        Render pages file from minio
        Args:
            pages: pages list of the image
            bucket: bucket name, existing in minio
            minio_path: file path, existing in minio
            local_path: path for saving files from minio
        Returns:
            Return None object
        """
        if not local_path.exists():
            local_path.mkdir()
        minio_file_path = (
            Path(minio_path) / Path(self.file_name)
            if not minio_path.suffix
            else minio_path
        )
        MinioCommunicator().download_file(
            bucket,
            str(minio_file_path),
            Path(local_path) / Path(minio_file_path.name),
        )
        self.render(pages, file_path=local_path / Path(minio_file_path.name))

    def name_image(self, file_name: str, page_number: int) -> str:
        """
        Create name of image in format 1.png
        Args:
            file_name: name of the file
            page_number: number of the page
        Returns:
            Return image name in format '<page number>/<image extension>'
        """

        return f"{file_name}_{page_number}.{self.image_format}"
