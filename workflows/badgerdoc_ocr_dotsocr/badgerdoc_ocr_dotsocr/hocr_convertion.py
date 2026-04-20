from typing import Iterable, Literal

import markdown
from lxml import etree
from pydantic import BaseModel, RootModel


def _parse_table(text: str) -> etree.Element | None:
    if "<table" not in text.lower():
        return None

    try:
        table_fragment = etree.fromstring(text, etree.HTMLParser())
        return table_fragment.find(".//table")
    except Exception:
        return None


def _extract_markdown_results(
    element: etree._Element,
) -> Iterable[str | etree._Element]:
    """Recursively yield text and inline elements from markdown HTML."""
    if element.tag in {
        "p",
        "ul",
        "ol",
        "li",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }:
        if element.text:
            yield element.text
        for child in element:
            yield from _extract_markdown_results(child)
    else:
        yield element


def _parse_markdown(text: str) -> list[str | etree._Element]:
    html_text = markdown.markdown(text)
    parser = etree.HTMLParser()
    html_fragment = etree.fromstring(f"<div>{html_text}</div>", parser)

    div_element = html_fragment.find(".//div")
    if div_element is None:
        return []

    return list(_extract_markdown_results(div_element))


def _normalize_bbox(bbox: list[int], width: int, height: int) -> list[int]:
    if width == 0 or height == 0:
        return bbox
    x1, y1, x2, y2 = bbox
    return [
        int(round(x1 * 1000 / width)),
        int(round(y1 * 1000 / height)),
        int(round(x2 * 1000 / width)),
        int(round(y2 * 1000 / height)),
    ]


class LayoutElement(BaseModel):
    bbox: list[int]
    category: Literal[
        "Caption",
        "Footnote",
        "Formula",
        "List-item",
        "Page-footer",
        "Page-header",
        "Picture",
        "Section-header",
        "Table",
        "Text",
        "Title",
    ]
    text: str | None = None

    def to_hocr_element(
        self, element_id: str, page_width: int, page_height: int
    ) -> etree.Element:
        hocr_class = "ocr_carea"
        tag = "div"

        norm_bbox = _normalize_bbox(self.bbox, page_width, page_height)
        bbox_str = "bbox " + " ".join(map(str, norm_bbox))

        container = etree.Element(
            tag,
            attrib={"class": hocr_class, "id": element_id, "title": bbox_str},
        )

        if self.category == "Picture":
            return container

        # Area -> Paragraph (ocr_par) -> Line (ocr_line)
        p = etree.SubElement(
            container,
            "p",
            attrib={
                "class": "ocr_par",
                "id": f"par_{element_id}",
                "title": bbox_str,
            },
        )
        line = etree.SubElement(
            p,
            "span",
            attrib={
                "class": "ocr_line",
                "id": f"line_{element_id}",
                "title": bbox_str,
            },
        )

        if not self.text:
            return container

        if self.category == "Table":
            table_node = _parse_table(self.text)
            if table_node is not None:
                line.append(table_node)
                return container

        for item in _parse_markdown(self.text):
            if isinstance(item, str):
                if len(line) > 0:
                    line[-1].tail = (line[-1].tail or "") + item
                elif line.text is None:
                    line.text = item
                else:
                    line.text += item
            else:
                line.append(item)
        return container


class LayoutResponse(RootModel):
    root: list[LayoutElement]

    def to_hocr(
        self,
        width: int,
        height: int,
        page_number: int = 1,
        model_name: str = "rednote-hilab-dots-ocr",
    ) -> str:
        html = etree.Element(
            "html",
            xmlns="http://www.w3.org/1999/xhtml",
            attrib={
                "{http://www.w3.org/XML/1998/namespace}lang": "en",
                "lang": "en",
            },
        )
        head = etree.SubElement(html, "head")
        etree.SubElement(
            head, "meta", attrib={"name": "ocr-system", "content": model_name}
        )

        capabilities = [
            "ocr_page",
            "ocr_carea",
            "ocr_par",
            "ocr_line",
        ]
        etree.SubElement(
            head,
            "meta",
            attrib={
                "name": "ocr-capabilities",
                "content": " ".join(capabilities),
            },
        )

        body = etree.SubElement(html, "body")

        page_bbox = f"bbox 0 0 {width} {height}"
        page_div = etree.SubElement(
            body,
            "div",
            attrib={
                "class": "ocr_page",
                "id": f"page_{page_number}",
                "title": f"image 'page_{page_number}.png'; {page_bbox}; ppageno {page_number-1}",
            },
        )

        for i, element in enumerate(self.root, start=1):
            hocr_el = element.to_hocr_element(
                f"block_{page_number}_{i}", width, height
            )
            page_div.append(hocr_el)

        return etree.tostring(
            html,
            pretty_print=True,
            method="xml",
            encoding="UTF-8",
            doctype='<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
        ).decode("utf-8")
