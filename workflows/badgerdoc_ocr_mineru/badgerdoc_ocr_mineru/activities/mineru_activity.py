import json
import logging
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from temporalio import activity

from badgerdoc_common import badgerdoc_http, trigger
from badgerdoc_common.activities import document
from badgerdoc_common.hocr import BadgerdocHOCRPageResult

logger = logging.getLogger(__name__)

OcrPath = str


@dataclass
class MineruOCRResult:
    content_list: OcrPath
    middle_json: OcrPath


@activity.defn
async def mineru_ocr_activity(
    params: trigger.DocumentTriggerParams,
    page: trigger.BadgerdocDocumentPage,
) -> MineruOCRResult:
    # Import modules inside function to avoid Temporal startup validation issues
    # pylint: disable=import-outside-toplevel
    from mineru.cli import common as mineru_common
    from mineru.utils import enum_class as mineru_enum
    from mineru.utils import pdf_image_tools as mineru_image_tools

    from badgerdoc_common import storage

    extraction_obj = params.target_extraction
    current_tags = extraction_obj.tags or []

    if "mineru-ocr" not in current_tags:
        logger.info(
            "Adding 'mineru-ocr' tag to extraction %s", extraction_obj.id
        )
        updated_tags = current_tags + ["mineru-ocr"]
        endpoint = f"/badgerdoc/extraction/{extraction_obj.id}/"
        await badgerdoc_http.badgerdoc_patch(endpoint, {"tags": updated_tags})

    document_to_ocr = await document.badgerdoc_get_rendition(
        page.document, page.page_num
    )

    buffer = BytesIO()
    await badgerdoc_http.badgerdoc_download(buffer, document_to_ocr)
    pdf_bytes = buffer.getvalue()

    with tempfile.TemporaryDirectory(prefix="mineru_ocr_") as temp_dir:
        if (
            document_to_ocr.extension
            and document_to_ocr.extension.lower()
            in mineru_common.image_suffixes
        ):
            pdf_bytes = mineru_image_tools.images_bytes_to_pdf_bytes(pdf_bytes)

        mineru_common.do_parse(
            output_dir=temp_dir,
            pdf_file_names=[str(document_to_ocr.id)],
            pdf_bytes_list=[pdf_bytes],
            p_lang_list=["en"],
            backend="pipeline",
            parse_method="auto",
            formula_enable=True,
            table_enable=True,
            f_dump_md=False,
            f_dump_content_list=True,
            f_dump_middle_json=True,
            f_dump_model_output=False,
            f_dump_orig_pdf=False,
            f_draw_layout_bbox=False,
            f_draw_span_bbox=False,
            f_make_md_mode=mineru_enum.MakeMode.MM_MD,
        )

        try:
            base_output_dir = Path(temp_dir) / str(document_to_ocr.id)
            content_list_path = None

            for subdir in ["pipeline", "auto"]:
                potential_path = (
                    base_output_dir
                    / subdir
                    / f"{document_to_ocr.id}_content_list.json"
                )
                if potential_path.exists():
                    content_list_path = potential_path
                    break

            if content_list_path:
                with open(content_list_path, "r", encoding="utf-8") as f:
                    content_list = json.load(f)

                type_counts = {}
                text_content = []
                for item in content_list:
                    content_type = item.get("type", "unknown")
                    type_counts[content_type] = (
                        type_counts.get(content_type, 0) + 1
                    )

                    if content_type in ["text", "title"] and "text" in item:
                        text_content.append(item["text"][:100])

            else:
                logger.warning(
                    "OCR content list file not found in: %s", base_output_dir
                )
                if base_output_dir.exists():
                    for file_path in base_output_dir.rglob("*"):
                        if file_path.is_file():
                            logger.info(
                                "  %s", file_path.relative_to(temp_dir)
                            )
        except Exception as e:
            logger.warning("Failed to read OCR results: %s", e)

        workflow_run_id = activity.info().workflow_run_id

        storage_params = storage.StorageWorkflowParams(
            workflow_package="badgerdoc_ocr_mineru",
            workflow_name=params.workflow.temporal_workflow_type,
            workflow_id=workflow_run_id,
        )

        uploaded_files = {}

        if content_list_path and content_list_path.exists():
            with open(content_list_path, "rb") as f:
                buffer = BytesIO(f.read())
            s3_path = await storage.badgerdoc_store_perm(
                buffer,
                storage_params,
                f"page_{page.page_num}_content_list.json",
            )
            uploaded_files["content_list"] = s3_path

        middle_json_path = None
        if content_list_path:
            potential_middle_path = (
                content_list_path.parent / f"{document_to_ocr.id}_middle.json"
            )
            if potential_middle_path.exists():
                middle_json_path = potential_middle_path

        if middle_json_path:
            with open(middle_json_path, "rb") as f:
                buffer = BytesIO(f.read())
            s3_path = await storage.badgerdoc_store_perm(
                buffer, storage_params, f"page_{page.page_num}_middle.json"
            )
            uploaded_files["middle_json"] = s3_path

    return MineruOCRResult(
        content_list=uploaded_files["content_list"],
        middle_json=uploaded_files["middle_json"],
    )


@activity.defn
async def convert_to_hocr(
    params: trigger.DocumentTriggerParams,
    page: trigger.BadgerdocDocumentPage,
    paths: MineruOCRResult,
) -> BadgerdocHOCRPageResult:
    from badgerdoc_common import storage

    page_number = page.page_num

    workflow_run_id = activity.info().workflow_run_id

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_mineru",
        workflow_name=params.workflow.temporal_workflow_type,
        workflow_id=workflow_run_id,
    )

    middle_json_buffer = BytesIO()
    await storage.badgerdoc_download_perm(
        middle_json_buffer, storage_params, f"page_{page_number}_middle.json"
    )
    middle_json_buffer.seek(0)
    middle_json = json.load(middle_json_buffer)

    page_idx = page_number - 1

    pdf_info = middle_json.get("pdf_info", [])
    if not pdf_info:
        raise ValueError("No PDF info found in middle.json")

    if len(pdf_info) > 1:
        logger.warning(
            "convert_to_hocr doesn't support multipage documents. "
            "middle.json contains %d pages, but only the first page will be processed.",
            len(pdf_info),
        )

    page_info = pdf_info[0]

    pdf_page_size = page_info.get("page_size")
    if not pdf_page_size:
        raise ValueError(
            f"page_size not found in middle.json for page {page_idx}"
        )
    page_width = pdf_page_size[0]
    page_height = pdf_page_size[1]

    page_items = page_info.get("para_blocks", [])
    discarded_items = page_info.get("discarded_blocks", [])

    all_items = []
    for item in page_items:
        all_items.append((item, False))
    for item in discarded_items:
        all_items.append((item, True))

    page_hocr_lines = [
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
        '<html xmlns="http://www.w3.org/1999/xhtml" lang="en">',
        "<head>",
        '<meta name="ocr-system" content="mineru"/>',
        '<meta name="ocr-capabilities" content="ocr_page ocr_carea ocr_par ocr_line ocr_section ocr_header ocr_image ocr_photo"/>',
        "</head>",
        "<body>",
    ]

    page_id = f"page_{page_number}"
    page_hocr_lines.append(
        f'<div class="ocr_page" id="{page_id}" title="bbox 0 0 1000 1000; ppageno {page_idx}">'
    )

    block_id = 1
    for item, is_discarded in all_items:
        item_type = item.get("type", "text")
        bbox = item.get("bbox", [0, 0, page_width, page_height])
        bbox_str = _to_normalized(bbox, page_width, page_height)

        block_elem_id = f"block_{page_number}_{block_id}"

        page_hocr_lines.append(
            f'<div class="ocr_carea" id="{block_elem_id}" title="bbox {bbox_str}">'
        )

        if item_type == "list":
            page_hocr_lines.append("<ul>")

            line_id = 1
            for line in item.get("lines", []):
                line_bbox = line.get("bbox", bbox)
                line_bbox_str = _to_normalized(
                    line_bbox, page_width, page_height
                )

                text_parts = []
                for span in line.get("spans", []):
                    if span.get("type") == "text":
                        text_parts.append(span.get("content", ""))
                text = " ".join(text_parts).strip()

                if text:
                    li_elem_id = f"line_{block_elem_id}_{line_id}"
                    page_hocr_lines.append(
                        f'<li class="ocr_line" id="{li_elem_id}" title="bbox {line_bbox_str}">{_escape_html(text)}</li>'
                    )
                    line_id += 1

            page_hocr_lines.append("</ul>")

        elif item_type in ["text", "title"] or is_discarded:
            par_elem_id = f"par_{block_elem_id}"

            if is_discarded:
                par_class = "ocr_discarded"
            elif item_type == "title":
                par_class = "ocr_header"
            else:
                par_class = "ocr_par"

            page_hocr_lines.append(
                f'<p class="{par_class}" id="{par_elem_id}" title="bbox {bbox_str}">'
            )

            line_id = 1
            for line in item.get("lines", []):
                line_bbox = line.get("bbox", bbox)
                line_bbox_str = _to_normalized(
                    line_bbox, page_width, page_height
                )

                text_parts = []
                for span in line.get("spans", []):
                    if span.get("type") == "text":
                        text_parts.append(span.get("content", ""))
                text = " ".join(text_parts).strip()

                if text:
                    line_elem_id = f"line_{block_elem_id}_{line_id}"
                    page_hocr_lines.append(
                        f'<span class="ocr_line" id="{line_elem_id}" title="bbox {line_bbox_str}">{_escape_html(text)}</span>'
                    )
                    line_id += 1

            page_hocr_lines.append("</p>")

        elif item_type == "image":
            img_path = ""
            for line in item.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("type") == "image":
                        img_path = span.get("image_path", "")
                        break
                if img_path:
                    break

            photo_elem_id = f"photo_{block_elem_id}"
            page_hocr_lines.append(
                f'<div class="ocr_photo" id="{photo_elem_id}" title="bbox {bbox_str}; image {img_path}"></div>'
            )

        else:
            par_elem_id = f"par_{block_elem_id}"
            page_hocr_lines.append(
                f'<p class="ocr_par" id="{par_elem_id}" title="bbox {bbox_str}">'
            )

            line_id = 1
            for line in item.get("lines", []):
                line_bbox = line.get("bbox", bbox)
                line_bbox_str = _to_normalized(
                    line_bbox, page_width, page_height
                )

                text_parts = []
                for span in line.get("spans", []):
                    if span.get("type") == "text":
                        text_parts.append(span.get("content", ""))
                text = " ".join(text_parts).strip()

                if text:
                    line_elem_id = f"line_{block_elem_id}_{line_id}"
                    page_hocr_lines.append(
                        f'<span class="ocr_line" id="{line_elem_id}" title="bbox {line_bbox_str}">{_escape_html(text)}</span>'
                    )
                    line_id += 1

            page_hocr_lines.append("</p>")

        page_hocr_lines.append("</div>")
        block_id += 1

    page_hocr_lines.append("</div>")
    page_hocr_lines.append("</body>")
    page_hocr_lines.append("</html>")

    page_hocr_content = "\n".join(page_hocr_lines)

    hocr_buffer = BytesIO(page_hocr_content.encode("utf-8"))
    hocr_path = await storage.badgerdoc_store_perm(
        hocr_buffer, storage_params, f"page_{page_number}.hocr"
    )

    return BadgerdocHOCRPageResult(h_ocr={str(page_number): hocr_path})


def _to_normalized(bbox, page_width, page_height):
    x1, y1, x2, y2 = bbox
    norm_x1 = int((x1 / page_width) * 1000)
    norm_y1 = int((y1 / page_height) * 1000)
    norm_x2 = int((x2 / page_width) * 1000)
    norm_y2 = int((y2 / page_height) * 1000)
    return f"{norm_x1} {norm_y1} {norm_x2} {norm_y2}"


def _escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
