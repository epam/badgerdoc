import re
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from lxml import etree
from PIL import Image

from badgerdoc.models import document

HOCR_MAX = 1000


class RenditionMissingSizeError(Exception):
    pass


def extract_bbox_from_hocr(
    content: str, xpath: str
) -> tuple[int, int, int, int]:
    if not content:
        raise ValueError("Content is empty")

    tree = etree.HTML(content)
    nodes = tree.xpath(xpath)
    if not nodes:
        raise ValueError(f"XPath '{xpath}' does not match any nodes")
    node = nodes[0]
    if not hasattr(node, "get"):
        raise ValueError(f"XPath '{xpath}' did not match an element node")

    title = node.get("title", "")
    match = re.search(r"bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", title)
    if not match:
        raise ValueError(
            f"Element matched by '{xpath}' has no bbox in its title attribute"
        )

    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        int(match.group(4)),
    )


def find_existing_chunk(
    document_id: int, page_num: int, coordinates_str: str
) -> document.Document | None:
    return document.Document.objects.filter(
        parent_document=document_id,
        tags__contains=["chunk"],
        metadata__page=page_num,
        metadata__position_in_parent=coordinates_str,
    ).first()


def _scale_hocr_to_pixels(
    hocr_coords: tuple[int, int, int, int],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = hocr_coords
    return (
        round(x1 * width / HOCR_MAX),
        round(y1 * height / HOCR_MAX),
        round(x2 * width / HOCR_MAX),
        round(y2 * height / HOCR_MAX),
    )


def crop_image(
    image_bytes: bytes, x1: int, y1: int, x2: int, y2: int
) -> bytes:
    img_buffer = BytesIO(image_bytes)
    image = Image.open(img_buffer)
    cropped = image.crop((x1, y1, x2, y2))
    output_buffer = BytesIO()
    cropped.save(output_buffer, format="PNG")
    return output_buffer.getvalue()


def crop_rendition(
    rendition: document.Document, x1: int, y1: int, x2: int, y2: int
) -> bytes:
    metadata = rendition.metadata or {}
    size = metadata.get("size")
    if not size or "width" not in size or "height" not in size:
        raise RenditionMissingSizeError(
            "Rendition document is missing size metadata"
        )
    px1, py1, px2, py2 = _scale_hocr_to_pixels(
        (x1, y1, x2, y2), size["width"], size["height"]
    )
    with rendition.file.open("rb") as f:
        image_bytes = f.read()
    return crop_image(image_bytes, px1, py1, px2, py2)


def create_chunk_document(
    document_obj: document.Document,
    user: User,
    page_num: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    png_bytes: bytes,
) -> document.Document:
    coordinates_str = f"{x1} {y1} {x2} {y2}"
    chunk_name = f"{document_obj.name or document_obj.id}_chunk_p{page_num}_{x1}_{y1}_{x2}_{y2}"
    chunk_doc = document.Document.objects.create(
        name=chunk_name,
        extension="png",
        uploaded_by=user,
        parent_document=document_obj,
        tags=["chunk"],
        metadata={"page": page_num, "position_in_parent": coordinates_str},
    )
    chunk_doc.file.save(
        f"{chunk_name}.png",
        ContentFile(png_bytes),
        save=True,
    )
    return chunk_doc
