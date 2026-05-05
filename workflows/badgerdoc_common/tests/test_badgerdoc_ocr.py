import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("BADGERDOC_REST_API_RETRY_POLICY", "1,2.0,30,3")
os.environ.setdefault("TEMPORAL_BADGERDOC_ADDRESS", "http://test:8000")
os.environ.setdefault("BADGERDOC_TOKEN", "test_token")
os.environ.setdefault("TEMPORAL_ADDRESS", "localhost:7233")
os.environ.setdefault("BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT", "5")

from badgerdoc_common import trigger
from badgerdoc_common.activities import document as doc_module
from badgerdoc_common.activities.document import (
    BadgerdocDocument,
    DocumentChunkRequest,
    ListDocumentsResponse,
)
from badgerdoc_common.activities.extraction import (
    BadgerdocExtractionPage,
    BadgerdocExtractionXpath,
)
from badgerdoc_common.badgerdoc_ocr import (
    OCRPageContainer,
    trigger_params_to_ocr_page,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_params(**kwargs) -> trigger.DocumentTriggerParams:
    return trigger.DocumentTriggerParams(
        workflow=MagicMock(),
        original_document=MagicMock(),
        target_extraction=MagicMock(),
        llm_params="",
        **kwargs,
    )


def _make_document(
    doc_id: int, parent_id: int | None = None
) -> BadgerdocDocument:
    return BadgerdocDocument(id=doc_id, parent_document_id=parent_id)


def _make_rendition(doc_id: int, page_num: int) -> BadgerdocDocument:
    return BadgerdocDocument(
        id=doc_id, metadata={"page": page_num}, tags=["rendition"]
    )


def _make_activity_mock(dispatch: dict) -> AsyncMock:
    """
    Return an AsyncMock for ``workflow.execute_activity`` that routes
    calls to per-activity return values based on the first argument.

    ``dispatch`` maps activity function → return value (or a list of
    sequential return values when the value is a list).
    """
    call_counters: dict = {fn: 0 for fn in dispatch}

    async def side_effect(fn, *args, **kwargs):
        if fn not in dispatch:
            raise ValueError(
                f"Unexpected activity in test: {getattr(fn, '__name__', fn)}"
            )
        value = dispatch[fn]
        if isinstance(value, list):
            idx = call_counters[fn]
            call_counters[fn] += 1
            return value[idx]
        return value

    return AsyncMock(side_effect=side_effect)


EXECUTE_ACTIVITY = "temporalio.workflow.execute_activity"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_params_returns_empty_container():
    params = _make_params()
    result = await trigger_params_to_ocr_page(params)
    assert result == OCRPageContainer(pages=[], blocks=[])


@pytest.mark.asyncio
async def test_linked_documents_expanded_to_rendition_pages():
    doc = _make_document(1)
    rendition_info_1 = _make_rendition(10, page_num=1)
    rendition_info_2 = _make_rendition(11, page_num=2)
    fetched_1 = _make_rendition(10, page_num=1)
    fetched_2 = _make_rendition(11, page_num=2)

    params = _make_params(linked_documents=[doc])

    mock = _make_activity_mock(
        {
            doc_module.badgerdoc_list_documents: ListDocumentsResponse(
                documents=[rendition_info_1, rendition_info_2], count=2
            ),
            doc_module.badgerdoc_get_rendition: [fetched_1, fetched_2],
        }
    )

    with patch(EXECUTE_ACTIVITY, new=mock):
        result = await trigger_params_to_ocr_page(params)

    assert len(result.pages) == 2
    assert len(result.blocks) == 0
    page_nums = {r.badgerdoc_document.page_num for r in result.pages}
    assert page_nums == {1, 2}
    result_docs = [r.badgerdoc_document.document for r in result.pages]
    assert fetched_1 in result_docs
    assert fetched_2 in result_docs


@pytest.mark.asyncio
async def test_linked_documents_rendition_missing_page_skipped(caplog):
    doc = _make_document(1)
    bad_rendition = BadgerdocDocument(id=99, metadata={})
    good_rendition = _make_rendition(10, page_num=1)
    fetched = _make_rendition(10, page_num=1)

    params = _make_params(linked_documents=[doc])

    mock = _make_activity_mock(
        {
            doc_module.badgerdoc_list_documents: ListDocumentsResponse(
                documents=[bad_rendition, good_rendition], count=2
            ),
            doc_module.badgerdoc_get_rendition: fetched,
        }
    )

    caplog.set_level(logging.ERROR, logger="badgerdoc_common.badgerdoc_ocr")
    with patch(EXECUTE_ACTIVITY, new=mock):
        result = await trigger_params_to_ocr_page(params)

    assert len(result.pages) == 1
    assert "no page in metadata" in caplog.text


@pytest.mark.asyncio
async def test_linked_document_pages_added():
    rendition = _make_document(10, parent_id=1)
    doc_page = trigger.BadgerdocDocumentPage(page_num=3, document=rendition)
    params = _make_params(linked_document_pages=[doc_page])

    result = await trigger_params_to_ocr_page(params)

    assert len(result.pages) == 1
    assert result.pages[0].badgerdoc_document.page_num == 3
    assert result.pages[0].badgerdoc_document.document is rendition
    assert len(result.blocks) == 0


@pytest.mark.asyncio
async def test_linked_document_pages_duplicate_skipped(caplog):
    original_doc = _make_document(1)
    rendition_info = _make_rendition(10, page_num=1)
    fetched = _make_rendition(10, page_num=1)

    duplicate_rendition = _make_document(10, parent_id=1)
    dup_page = trigger.BadgerdocDocumentPage(
        page_num=1, document=duplicate_rendition
    )

    params = _make_params(
        linked_documents=[original_doc],
        linked_document_pages=[dup_page],
    )

    mock = _make_activity_mock(
        {
            doc_module.badgerdoc_list_documents: ListDocumentsResponse(
                documents=[rendition_info], count=1
            ),
            doc_module.badgerdoc_get_rendition: fetched,
        }
    )

    caplog.set_level(logging.WARNING, logger="badgerdoc_common.badgerdoc_ocr")
    with patch(EXECUTE_ACTIVITY, new=mock):
        result = await trigger_params_to_ocr_page(params)

    assert len(result.pages) == 1
    assert "already added from linked_documents" in caplog.text


@pytest.mark.asyncio
async def test_linked_document_pages_non_duplicate_added():
    original_doc = _make_document(1)
    rendition_info = _make_rendition(10, page_num=1)
    fetched = _make_rendition(10, page_num=1)

    other_rendition = _make_document(20, parent_id=2)
    other_page = trigger.BadgerdocDocumentPage(
        page_num=1, document=other_rendition
    )

    params = _make_params(
        linked_documents=[original_doc],
        linked_document_pages=[other_page],
    )

    mock = _make_activity_mock(
        {
            doc_module.badgerdoc_list_documents: ListDocumentsResponse(
                documents=[rendition_info], count=1
            ),
            doc_module.badgerdoc_get_rendition: fetched,
        }
    )

    with patch(EXECUTE_ACTIVITY, new=mock):
        result = await trigger_params_to_ocr_page(params)

    assert len(result.pages) == 2


@pytest.mark.asyncio
async def test_linked_extraction_xpaths_become_blocks():
    ext_page = BadgerdocExtractionPage(
        id=5, extraction_id=3, page_number=2, document_id=1
    )
    xpath_obj = BadgerdocExtractionXpath(
        extraction_page=ext_page, xpath="//div[@id='block-1']"
    )
    chunk_doc = _make_document(99)

    params = _make_params(linked_extraction_xpaths=[xpath_obj])

    mock = _make_activity_mock(
        {
            doc_module.badgerdoc_get_document_chunk: chunk_doc,
        }
    )

    with patch(EXECUTE_ACTIVITY, new=mock):
        result = await trigger_params_to_ocr_page(params)

    assert len(result.pages) == 0
    assert len(result.blocks) == 1
    assert result.blocks[0].badgerdoc_document.page_num == 2
    assert result.blocks[0].badgerdoc_document.document is chunk_doc


@pytest.mark.asyncio
async def test_linked_extraction_xpaths_chunk_request_args():
    ext_page = BadgerdocExtractionPage(
        id=5, extraction_id=3, page_number=2, document_id=7
    )
    xpath_obj = BadgerdocExtractionXpath(
        extraction_page=ext_page, xpath="//p[1]"
    )
    chunk_doc = _make_document(99)

    params = _make_params(linked_extraction_xpaths=[xpath_obj])

    mock = _make_activity_mock(
        {
            doc_module.badgerdoc_get_document_chunk: chunk_doc,
        }
    )

    with patch(EXECUTE_ACTIVITY, new=mock):
        await trigger_params_to_ocr_page(params)

    # Find the call for badgerdoc_get_document_chunk and assert its argument
    chunk_calls = [
        c
        for c in mock.call_args_list
        if c.args[0] is doc_module.badgerdoc_get_document_chunk
    ]
    assert len(chunk_calls) == 1
    assert chunk_calls[0].args[1] == DocumentChunkRequest(
        document_id=7,
        page_num=2,
        extraction_id=3,
        xpath="//p[1]",
    )


@pytest.mark.asyncio
async def test_all_sources_combined():
    doc = _make_document(1)
    rendition_info = _make_rendition(10, page_num=1)
    fetched = _make_rendition(10, page_num=1)

    other_rendition = _make_document(20, parent_id=2)
    doc_page = trigger.BadgerdocDocumentPage(
        page_num=5, document=other_rendition
    )

    ext_page = BadgerdocExtractionPage(
        id=1, extraction_id=1, page_number=1, document_id=1
    )
    xpath_obj = BadgerdocExtractionXpath(
        extraction_page=ext_page, xpath="//span"
    )
    chunk_doc = _make_document(99)

    params = _make_params(
        linked_documents=[doc],
        linked_document_pages=[doc_page],
        linked_extraction_xpaths=[xpath_obj],
    )

    mock = _make_activity_mock(
        {
            doc_module.badgerdoc_list_documents: ListDocumentsResponse(
                documents=[rendition_info], count=1
            ),
            doc_module.badgerdoc_get_rendition: fetched,
            doc_module.badgerdoc_get_document_chunk: chunk_doc,
        }
    )

    with patch(EXECUTE_ACTIVITY, new=mock):
        result = await trigger_params_to_ocr_page(params)

    assert len(result.pages) == 2
    assert len(result.blocks) == 1
