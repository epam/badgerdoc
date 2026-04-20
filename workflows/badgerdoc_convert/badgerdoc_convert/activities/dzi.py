import logging
import math
import os
import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from temporalio import activity

from badgerdoc_common import badgerdoc_http
from badgerdoc_common.activities import document

MAX_TILE_WIDTH = 2048
TILE_SIZE = 2048


logger = logging.getLogger(__name__)


@dataclass
class TileData:
    path: str
    document_id: int
    tags: list[str]


@dataclass
class PyramidLevelResult:
    tiles_created: int
    grid_size: tuple[int, int]
    tile_data: list[TileData]


@dataclass
class DZIConvertResult:
    dzi_document_id: int
    dzi_tags: list[str]
    tiles: list[TileData]
    total_tiles_created: int


class DZIConverter:
    def __init__(self, tile_size=TILE_SIZE):
        self.tile_size = tile_size

    def calculate_tile_dimensions(
        self, image_width: int, image_height: int
    ) -> tuple[int, int, int, int]:
        cols = math.ceil(image_width / MAX_TILE_WIDTH)
        tile_width = math.ceil(image_width / cols)
        aspect_ratio = image_height / image_width
        tile_height = math.ceil(tile_width * aspect_ratio)
        rows = math.ceil(image_height / tile_height)
        return tile_width, tile_height, cols, rows

    def calculate_pyramid_levels(
        self, image_width: int, image_height: int
    ) -> int:
        max_dim = max(image_width, image_height)
        return math.ceil(math.log2(max_dim)) + 1

    async def create_pyramid_level(
        self,
        image: Image.Image,
        level: int,
        max_level: int,
        source_document: document.BadgerdocDocument,
    ) -> PyramidLevelResult:

        scale = 2 ** (max_level - level)

        scaled_width = max(1, math.ceil(image.width / scale))
        scaled_height = max(1, math.ceil(image.height / scale))

        tile_width = self.tile_size

        scaled_image = image.resize(
            (scaled_width, scaled_height), Image.Resampling.LANCZOS
        )

        cols = math.ceil(scaled_width / tile_width)
        rows = math.ceil(scaled_height / tile_width)

        tiles_created = 0
        tile_data: list[TileData] = []

        for row in range(rows):
            for col in range(cols):
                left = col * tile_width
                top = row * tile_width
                right = min(left + tile_width, scaled_width)
                bottom = min(top + tile_width, scaled_height)

                if right > left and bottom > top:
                    tile = scaled_image.crop((left, top, right, bottom))

                    tile_path = f"{level}/{col}_{row}.png"

                    tile_buffer = BytesIO()
                    tile.save(tile_buffer, "PNG")
                    tile_buffer.seek(0)

                    page = source_document.metadata.get("page")
                    if page is None:
                        logger.warning(
                            "Page on rendition metadata is not specified: %s",
                            source_document.metadata,
                        )
                        logger.warning("Setting default page")
                        page = 1

                    uploaded_doc = await badgerdoc_http.badgerdoc_upload(
                        tile_buffer,
                        f"{level}_{col}_{row}.png",
                        metadata={"page": page},
                        tags=["dzi", tile_path],
                        parent_document_id=source_document.id,
                        extension="png",
                    )

                    logger.info("Uploaded tile: %s", uploaded_doc)

                    tile_data.append(
                        TileData(
                            path=tile_path,
                            document_id=uploaded_doc["id"],
                            tags=["dzi", tile_path],
                        )
                    )

                    tiles_created += 1

        return PyramidLevelResult(
            tiles_created=tiles_created,
            grid_size=(cols, rows),
            tile_data=tile_data,
        )

    def create_dzi_xml(self, image_width, image_height):
        root = ET.Element("Image")
        root.set("xmlns", "http://schemas.microsoft.com/deepzoom/2008")
        root.set("Format", "png")
        root.set("Overlap", "0")
        root.set("TileSize", str(self.tile_size))

        size = ET.SubElement(root, "Size")
        size.set("Width", str(image_width))
        size.set("Height", str(image_height))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)

        buffer = BytesIO()
        tree.write(buffer, encoding="utf-8", xml_declaration=True)
        buffer.seek(0)
        return buffer

    async def clear_previous_tiles(
        self, source_document: document.BadgerdocDocument
    ) -> None:
        logger.info("Deleting tiles for document: %s", source_document.id)

        list_request = document.ListDocumentsRequest(
            tags=["dzi"], parent_document_id=source_document.id
        )

        existing_docs = await document.badgerdoc_list_documents(list_request)
        logger.info("Found documents: %s", existing_docs)

        for existing_doc in existing_docs.documents:
            logger.info("Deleting existing DZI document: %s", existing_doc.id)
            await document.badgerdoc_delete_document(existing_doc.id)

    async def create_tiles(
        self, source_document: document.BadgerdocDocument, image_: BytesIO
    ) -> DZIConvertResult:

        logger.info("Creating tiles for document: %s", source_document.id)

        image_ = Image.open(image_)  # type: ignore
        image_width, image_height = image_.size

        logger.info("Image size: %sx%s", image_width, image_height)

        dzi_filename = f"{source_document.id}_image.dzi"
        dzi_buffer = self.create_dzi_xml(image_width, image_height)

        page = source_document.metadata.get("page")
        if page is None:
            logger.warning(
                "Page on rendition metadata is not specified: %s",
                source_document.metadata,
            )
            logger.warning("Setting default page")
            page = 1

        dzi_upload_result = await badgerdoc_http.badgerdoc_upload(
            dzi_buffer,
            dzi_filename,
            metadata={"page": page},
            tags=["dzi", "xml"],
            parent_document_id=source_document.id,
            extension="png",
        )

        levels = self.calculate_pyramid_levels(image_width, image_height)

        logger.info("Count of levels: %s", levels)

        all_tiles: list[TileData] = []
        total_tiles_created = 0

        for level in range(levels):
            result = await self.create_pyramid_level(
                image_, level, levels - 1, source_document  # type: ignore
            )

            logger.info(
                f"Level {level}: {result.tiles_created} tiles "
                f"({result.grid_size[0]}x{result.grid_size[1]} grid)"
            )

            all_tiles.extend(result.tile_data)
            total_tiles_created += result.tiles_created

        return DZIConvertResult(
            dzi_document_id=dzi_upload_result["id"],
            dzi_tags=["dzi", "xml"],
            tiles=all_tiles,
            total_tiles_created=total_tiles_created,
        )


@activity.defn
async def convert_to_dzi(
    source_document: document.BadgerdocDocument,
) -> DZIConvertResult:

    buffer = BytesIO()
    await badgerdoc_http.badgerdoc_download(buffer, source_document)
    dzi_conv = DZIConverter()
    result = await dzi_conv.create_tiles(source_document, buffer)

    return result
