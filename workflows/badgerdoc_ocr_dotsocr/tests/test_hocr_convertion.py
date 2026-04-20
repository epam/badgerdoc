import pytest
from hocr_spec import HocrSpec, HocrValidator
from lxml import etree

from badgerdoc_ocr_dotsocr.hocr_convertion import LayoutResponse


def validate_hocr(content: str):
    report = HocrValidator.Report("validate-hocr")
    HocrSpec().check(
        report,
        etree.HTML(content.encode("utf-8")),
    )

    if not report.is_valid():
        raise AssertionError(report.format("text"))


@pytest.mark.parametrize("page_number", [1, 5, 10])
def test_hocr_id_generation_with_page_numbers(page_number: int):
    """Tests that IDs are correctly generated using the page number."""
    data = [
        {"bbox": [0, 0, 100, 100], "category": "Text", "text": "Page content"}
    ]
    response = LayoutResponse.model_validate(data)

    hocr_output = response.to_hocr(
        width=1000, height=1000, page_number=page_number
    )
    validate_hocr(hocr_output)

    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(hocr_output.encode("utf-8"), parser=parser)
    ns = {"h": "http://www.w3.org/1999/xhtml"}

    page_div = root.find(".//h:div[@class='ocr_page']", ns)
    assert page_div.get("id") == f"page_{page_number}"

    block_div = root.find(".//h:div[@class='ocr_carea']", ns)
    assert block_div.get("id") == f"block_{page_number}_1"

    par_p = root.find(".//h:p[@class='ocr_par']", ns)
    assert par_p.get("id") == f"par_block_{page_number}_1"

    line_span = root.find(".//h:span[@class='ocr_line']", ns)
    assert line_span.get("id") == f"line_block_{page_number}_1"


@pytest.mark.parametrize(
    "category, expected_class, expected_tag",
    [
        # TODO: move back to full parsing once frontend supports it
        ("Caption", "ocr_carea", "div"),
        ("Footnote", "ocr_carea", "div"),
        ("Formula", "ocr_carea", "div"),
        ("List-item", "ocr_carea", "div"),
        ("Page-footer", "ocr_carea", "div"),
        ("Page-header", "ocr_carea", "div"),
        ("Picture", "ocr_carea", "div"),
        ("Section-header", "ocr_carea", "div"),
        ("Table", "ocr_carea", "div"),
        ("Text", "ocr_carea", "div"),
        ("Title", "ocr_carea", "div"),
    ],
)
def test_hocr_element_categories(
    category: str, expected_class: str, expected_tag: str
):
    """Tests that various categories result in correct hOCR classes."""
    data = [
        {
            "bbox": [10, 10, 50, 50],
            "category": category,
            "text": f"Content for {category}",
        }
    ]
    response = LayoutResponse.model_validate(data)

    hocr_output = response.to_hocr(width=100, height=100)
    validate_hocr(hocr_output)

    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(hocr_output.encode("utf-8"), parser=parser)
    ns = {"h": "http://www.w3.org/1999/xhtml"}

    element = root.find(f".//h:{expected_tag}[@id='block_1_1']", ns)
    assert element is not None
    assert element.get("class") == expected_class


def test_hocr_markdown_conversion():
    """Tests hOCR conversion with markdown in text and header elements."""
    data = [
        {
            "bbox": [4, 5, 93, 22],
            "category": "Section-header",
            "text": "# Assumptions",
        },
        {
            "bbox": [4, 36, 376, 69],
            "category": "Text",
            "text": "**Positioning** - we will still use int-based coordinates for bbox, but `bbox` ... coordinates will be in range `[0, 1000]`.",
        },
        {
            "bbox": [4, 85, 96, 99],
            "category": "Section-header",
            "text": "## Layout definition:",
        },
        {
            "bbox": [22, 116, 286, 129],
            "category": "List-item",
            "text": '* `ocr_carea` will be the root "block" definition.',
        },
        {
            "bbox": [22, 134, 363, 165],
            "category": "List-item",
            "text": "* Required capabilities: `ocrPhoto`, `ocr_page`, `ocr_carea`, `ocr_par`, `ocr_line`, `ocrx_word`. See documentation.",
        },
    ]
    response = LayoutResponse.model_validate(data)
    width, height = 1000, 1000

    hocr_output = response.to_hocr(width=width, height=height)
    print(hocr_output)

    validate_hocr(hocr_output)

    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(hocr_output.encode("utf-8"), parser=parser)
    ns = {"h": "http://www.w3.org/1999/xhtml"}

    header1 = root.find(".//h:div[@id='block_1_1']", ns)
    assert "Assumptions" in "".join(header1.itertext())
    assert "#" not in "".join(header1.itertext())

    text_block = root.find(".//h:div[@id='block_1_2']", ns)
    text_content = "".join(text_block.itertext())
    assert "**" not in text_content
    assert "`" not in text_content
    assert "Positioning" in text_content

    assert text_block.find(".//h:strong", ns) is not None
    assert text_block.find(".//h:code", ns) is not None

    list_item = root.find(".//h:div[@id='block_1_4']", ns)
    list_content = "".join(list_item.itertext())
    assert "*" not in list_content
    assert "ocr_carea" in list_content
    assert list_item.find(".//h:code", ns) is not None
