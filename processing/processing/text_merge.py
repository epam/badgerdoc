"""
Merging texts from small word bboxes to paragraph texts
according to annotations.
"""
import json
import logging
import tempfile
import traceback as tb
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from minio.error import MinioException

from processing import schema
from processing.schema import AnnotationData, MatchedPage, Page, ParagraphBbox
from processing.third_party_code.box_util import stitch_boxes_into_lines
from processing.third_party_code.table import BorderBox
from processing.utils.minio_utils import MinioCommunicator

logger = logging.getLogger(__name__)


def match_page(words: Dict[str, Any], page: Page) -> MatchedPage:
    """Match words bboxes to annotation bboxes."""
    matched_page = MatchedPage(page_num=page.page_num, paragraph_bboxes={})
    for raw_word_bbox in words["objs"]:
        if raw_word_bbox["type"] != "text":
            continue
        word_bbox = BorderBox(
            raw_word_bbox["bbox"][0],
            raw_word_bbox["bbox"][1],
            raw_word_bbox["bbox"][2],
            raw_word_bbox["bbox"][3],
        )

        for paragraph in page.objs:
            if word_bbox.box_is_inside_box(
                BorderBox(*(int(i) for i in paragraph["bbox"])), threshold=0.8
            ):
                nest_bbox = {
                    "x1": word_bbox.top_left_x,
                    "y1": word_bbox.top_left_y,
                    "x2": word_bbox.bottom_right_x,
                    "y2": word_bbox.bottom_right_y,
                    "text": raw_word_bbox["text"],
                }

                matched_page.paragraph_bboxes.setdefault(
                    paragraph["id"],
                    ParagraphBbox(bbox=paragraph["bbox"], nested_bboxes=[]),
                ).nested_bboxes.append(nest_bbox)
                break
    return matched_page


def convert_points_to_pixels(
    page: Dict[str, Any], new_width: float, new_height: float
) -> Dict[str, Any]:
    """Converts units of page size from word bboxes to
    units of annotation bboxes."""
    k_width = new_width / page["size"]["width"]
    k_height = new_height / page["size"]["height"]
    page["size"]["width"] = new_width
    page["size"]["height"] = new_height

    for text_box in page["objs"]:
        if text_box["type"] == "text":
            text_box["bbox"] = (
                round(text_box["bbox"][0] * k_width),
                round(text_box["bbox"][1] * k_height),
                round(text_box["bbox"][2] * k_width),
                round(text_box["bbox"][3] * k_height),
            )
    return page


def stitch_boxes(
    matched_pages: List[MatchedPage],
    annotations: List[Page],
    max_x_dist: int = 100,
) -> None:
    """Stitch texts from bboxes to union text."""
    logger.info("Stitching texts")
    pages_and_texts: Dict[int, Dict[int, str]] = {}

    for obj_page in matched_pages:
        for id_paragraph, paragraph in obj_page.paragraph_bboxes.items():
            boxes_for_stitch = []
            for text_bbox in paragraph.nested_bboxes:
                boxes_for_stitch.append(
                    {
                        "box": [
                            text_bbox["x1"],
                            text_bbox["y1"],
                            text_bbox["x2"],
                            text_bbox["y2"],
                        ],
                        "text": text_bbox["text"],
                    }
                )
            if obj_page.page_num not in pages_and_texts:
                pages_and_texts[obj_page.page_num] = {}
            pages_and_texts[obj_page.page_num][id_paragraph] = "\n".join(
                [
                    box["text"]
                    for box in stitch_boxes_into_lines(
                        boxes_for_stitch, max_x_dist=max_x_dist
                    )
                ]
            )
    for page in annotations:
        if page.page_num not in pages_and_texts.keys():
            continue
        for obj in page.objs:
            if obj["id"] not in pages_and_texts[page.page_num]:
                continue
            obj["text"] = pages_and_texts[page.page_num][obj["id"]]


def download_files(
    request_data: schema.AnnotationData, directory: Path
) -> Optional[Path]:
    """Download content of path from request to the directory."""
    communicator = MinioCommunicator()
    document: Path = Path(request_data.file)
    file_parent = directory / document.parent
    file_parent.mkdir(parents=True, exist_ok=True)
    communicator.client.fget_object(
        bucket_name=request_data.bucket,
        object_name=request_data.file,
        file_path=str(file_parent / document.name),
    )
    ocr_parent = None
    for obj in communicator.client.list_objects(
        bucket_name=request_data.bucket,
        prefix=str(request_data.input_path),
        recursive=True,
    ):
        ocr_parent = (directory / Path(obj.object_name)).parent
        ocr_parent.mkdir(parents=True, exist_ok=True)

        communicator.client.fget_object(
            bucket_name=request_data.bucket,
            object_name=obj.object_name,
            file_path=str(Path(ocr_parent) / Path(obj.object_name).name),
        )

    return ocr_parent


def download_ocr_result(
    request_data: schema.AnnotationData, dirname: Path
) -> Optional[Path]:
    try:
        return download_files(request_data, dirname)
    except MinioException as err:
        logger.error(
            "MinioProblem: %s",
            tb.format_exception(None, err, err.__traceback__),
        )
        raise HTTPException(400, detail=str(err)) from err


def merge_words_to_paragraph(request_data: AnnotationData) -> AnnotationData:
    """Merge words into paragraph:
    1. Download OCR result (separated words)
    2. Fill Paragraphs (text GeomObject) with words from OCR"""

    with tempfile.TemporaryDirectory() as dirname:
        if not (ocr_path := download_files(request_data, Path(dirname))):
            logger.info("No objects in minio: %s", request_data.file)
            return request_data

        matched_pages: List[MatchedPage] = []
        for page in request_data.input.pages:
            preprocessed_page = convert_points_to_pixels(
                page=json.loads(
                    (ocr_path / f"{page.page_num}.json").read_text()
                ),
                new_width=page.size.width,
                new_height=page.size.height,
            )
            matched_pages.append(match_page(preprocessed_page, page))

        stitch_boxes(matched_pages, request_data.input.pages)

    return request_data
