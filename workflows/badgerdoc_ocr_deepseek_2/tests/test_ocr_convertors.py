import os


os.environ.setdefault("BADGERDOC_REST_API_RETRY_POLICY", "1,2,10,3")

from badgerdoc_ocr_deepseek_2.activities.ocr_convertors import (  # noqa: E402
    _blocks_to_hocr,
    _classify_block,
    _parse_ocr_blocks,
    _safe_inline_html,
)

# ---------------------------------------------------------------------------
# _classify_block
# ---------------------------------------------------------------------------


def test_classify_block_table_by_ref_type():
    block = {
        "type": "table",
        "bbox": (0, 0, 100, 100),
        "raw": "anything",
        "lines": [],
    }
    assert _classify_block(block) == "table"


def test_classify_block_list_by_ref_type():
    for ref in ("list", "list-item", "List", "LIST-ITEM"):
        block = {
            "type": ref,
            "bbox": (0, 0, 100, 100),
            "raw": "anything",
            "lines": [],
        }
        assert _classify_block(block) == "list"


def test_classify_block_table_by_content_fallback():
    raw = "| Col A | Col B |\n|-------|-------|\n| 1     | 2     |"
    block = {
        "type": "text",
        "bbox": (0, 0, 100, 100),
        "raw": raw,
        "lines": [raw],
    }
    assert _classify_block(block) == "table"


def test_classify_block_list_bullet_fallback():
    raw = "* Item one\n* Item two"
    block = {
        "type": "paragraph",
        "bbox": (0, 0, 100, 100),
        "raw": raw,
        "lines": ["* Item one", "* Item two"],
    }
    assert _classify_block(block) == "list"


def test_classify_block_list_bullet_unicode_fallback():
    """Test that \u2022 (•) is recognized as a bullet marker."""
    block = {
        "type": "paragraph",
        "bbox": (0, 0, 100, 100),
        "raw": "• Item one\n• Item two",
        "lines": ["• Item one", "• Item two"],
    }
    assert _classify_block(block) == "list"


def test_classify_block_list_ordered_fallback():
    raw = "1. First\n2. Second"
    block = {
        "type": "paragraph",
        "bbox": (0, 0, 100, 100),
        "raw": raw,
        "lines": ["1. First", "2. Second"],
    }
    assert _classify_block(block) == "list"


def test_classify_block_text():
    block = {
        "type": "text",
        "bbox": (0, 0, 100, 100),
        "raw": "Hello world.",
        "lines": ["Hello world."],
    }
    assert _classify_block(block) == "text"


# ---------------------------------------------------------------------------
# _safe_inline_html
# ---------------------------------------------------------------------------


def test_safe_inline_html_preserves_sub():
    result = _safe_inline_html("H<sub>2</sub>O")
    assert "<sub>2</sub>" in result
    assert "&lt;sub&gt;" not in result


def test_safe_inline_html_preserves_sup():
    result = _safe_inline_html("E=mc<sup>2</sup>")
    assert "<sup>2</sup>" in result
    assert "&lt;sup&gt;" not in result


def test_safe_inline_html_escapes_other_tags():
    result = _safe_inline_html("<script>alert(1)</script>")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_safe_inline_html_escapes_ampersand():
    result = _safe_inline_html("A & B")
    assert "&amp;" in result


# ---------------------------------------------------------------------------
# _blocks_to_hocr — table rendering
# ---------------------------------------------------------------------------


def _make_table_block():
    raw = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |"
    lines = [line.strip() for line in raw.split('\n') if line.strip()]
    return {
        "type": "table",
        "bbox": (10, 20, 200, 100),
        "raw": raw,
        "lines": lines,
    }


def test_table_block_renders_table_element():
    hocr = "\n".join(_blocks_to_hocr(1, [_make_table_block()]))
    assert "<table" in hocr
    assert "Header 1" in hocr
    assert "Cell 1" in hocr


def test_table_block_wrapped_in_ocr_line():
    hocr = "\n".join(_blocks_to_hocr(1, [_make_table_block()]))
    assert 'class="ocr_line"' in hocr
    assert 'class="ocr_carea"' in hocr
    assert 'class="ocr_par"' in hocr


# ---------------------------------------------------------------------------
# _blocks_to_hocr — list rendering
# ---------------------------------------------------------------------------


def _make_list_block():
    raw = "* Item one\n* Item two\n* Item three"
    return {
        "type": "list",
        "bbox": (10, 200, 200, 300),
        "raw": raw,
        "lines": ["* Item one", "* Item two", "* Item three"],
    }


def test_list_block_renders_without_list_wrapper():
    """Test that list items are rendered as ocr_line spans without <ul>/<ol> wrapper."""
    hocr = "\n".join(_blocks_to_hocr(1, [_make_list_block()]))
    # Should NOT contain <ul> or <ol> tags
    assert "<ul" not in hocr
    assert "<ol" not in hocr
    # Should contain the text content (words are split into separate ocrx_word spans)
    assert "Item" in hocr
    assert "one" in hocr
    assert "two" in hocr
    assert "three" in hocr
    # Should have multiple ocr_line spans (one per list item)
    assert hocr.count('class="ocr_line"') == 3


def test_list_block_strips_bullet_markers():
    """Test that bullet markers are stripped from list items."""
    hocr = "\n".join(_blocks_to_hocr(1, [_make_list_block()]))
    # Bullet markers should be removed
    assert "* Item" not in hocr
    assert "*" not in hocr or 'title="bbox' in hocr  # * might appear in attributes
    # But the text content should remain
    assert "Item" in hocr
    assert "one" in hocr
    assert "two" in hocr


def test_list_block_with_unicode_bullet():
    """Test that unicode bullet markers (•) are recognized and stripped."""
    block = {
        "type": "list",
        "bbox": (10, 200, 200, 300),
        "raw": "• Item one\n• Item two",
        "lines": ["• Item one", "• Item two"],
    }
    hocr = "\n".join(_blocks_to_hocr(1, [block]))
    # Should not contain the bullet character
    assert "•" not in hocr
    # Should contain the text (words are split into separate ocrx_word spans)
    assert "Item" in hocr
    assert "one" in hocr
    assert "two" in hocr
    # Should have ocr_line spans
    assert hocr.count('class="ocr_line"') == 2


def test_list_block_wrapped_in_ocr_line():
    hocr = "\n".join(_blocks_to_hocr(1, [_make_list_block()]))
    assert 'class="ocr_line"' in hocr
    assert 'class="ocr_carea"' in hocr


# ---------------------------------------------------------------------------
# _blocks_to_hocr — sub-/superscript in plain text
# ---------------------------------------------------------------------------


def _make_text_block_with_sub():
    return {
        "type": "text",
        "bbox": (10, 300, 200, 320),
        "raw": "The formula H<sub>2</sub>O is water.",
        "lines": ["The formula H<sub>2</sub>O is water."],
    }


def test_text_with_sub_preserves_tag():
    hocr = "\n".join(_blocks_to_hocr(1, [_make_text_block_with_sub()]))
    assert "<sub>2</sub>" in hocr
    assert "&lt;sub&gt;" not in hocr


def test_text_with_sup_preserves_tag():
    block = {
        "type": "text",
        "bbox": (10, 300, 200, 320),
        "raw": "E=mc<sup>2</sup>",
        "lines": ["E=mc<sup>2</sup>"],
    }
    hocr = "\n".join(_blocks_to_hocr(1, [block]))
    assert "<sup>2</sup>" in hocr
    assert "&lt;sup&gt;" not in hocr


# ---------------------------------------------------------------------------
# _blocks_to_hocr — plain text word splitting regression
# ---------------------------------------------------------------------------


def test_plain_text_word_splitting_produces_ocrx_word():
    block = {
        "type": "text",
        "bbox": (10, 400, 210, 420),
        "raw": "Hello world",
        "lines": ["Hello world"],
    }
    hocr = "\n".join(_blocks_to_hocr(1, [block]))
    assert hocr.count('class="ocrx_word"') == 2
    assert "Hello" in hocr
    assert "world" in hocr


# ---------------------------------------------------------------------------
# _parse_ocr_blocks — raw field is stored
# ---------------------------------------------------------------------------


def test_parse_ocr_blocks_stores_raw():
    text = (
        "<|ref|>text<|/ref|><|det|>[[0, 0, 100, 50]]<|/det|>\n" "Hello world\n"
    )
    blocks = _parse_ocr_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["raw"] == "Hello world"


def test_parse_ocr_blocks_stores_raw_for_table():
    table_content = "| A | B |\n|---|---|\n| 1 | 2 |"
    text = (
        f"<|ref|>table<|/ref|><|det|>[[0, 0, 100, 50]]<|/det|>\n"
        f"{table_content}\n"
    )
    blocks = _parse_ocr_blocks(text)
    assert len(blocks) == 1
    assert "| A | B |" in blocks[0]["raw"]


# ---------------------------------------------------------------------------
# Mixed page — IDs are unique and sequential
# ---------------------------------------------------------------------------


def test_mixed_page_block_ids_are_unique():
    blocks = [
        _make_table_block(),
        _make_list_block(),
        {
            "type": "text",
            "bbox": (10, 400, 200, 420),
            "raw": "Plain text here.",
            "lines": ["Plain text here."],
        },
    ]
    hocr = "\n".join(_blocks_to_hocr(2, blocks))
    assert 'id="block_2_1"' in hocr
    assert 'id="block_2_2"' in hocr
    assert 'id="block_2_3"' in hocr
