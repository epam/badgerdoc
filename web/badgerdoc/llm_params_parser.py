import logging
from dataclasses import dataclass

from django.contrib.auth.models import User
from lxml import etree

from badgerdoc.models import document, extraction, extraction_page
from badgerdoc.models import extraction_helpers

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocParsedParams:
    linked_documents: list[document.Document]
    linked_extractions: list[extraction.Extraction] | None
    linked_extraction_pages: list[extraction_page.ExtractionPage] | None
    linked_extraction_xpaths: list[extraction_helpers.BadgerdocExtractionXpath] | None
    prompt_text: str


@dataclass
class ParsedReference:
    document_id: int
    page_number: int | None = None
    extraction_id: int | None = None
    xpath: str | None = None


def parse(user_id: int, llm_params: str) -> BadgerdocParsedParams:
    user = User.objects.get(id=user_id)

    references = extract_references(llm_params)
    validated_refs = validate_and_normalize_references(user, references)

    linked_docs = collect_documents(validated_refs)
    linked_exts = collect_extractions(validated_refs)
    linked_ext_pages = collect_extraction_pages(validated_refs)
    linked_xpaths = collect_xpaths(validated_refs)

    return BadgerdocParsedParams(
        linked_documents=linked_docs,
        linked_extractions=linked_exts if linked_exts else None,
        linked_extraction_pages=linked_ext_pages if linked_ext_pages else None,
        linked_extraction_xpaths=linked_xpaths if linked_xpaths else None,
        prompt_text=llm_params,
    )


def extract_references(llm_params: str) -> list[ParsedReference]:
    references = []
    start_marker = '{{/badgerdoc/'

    pos = 0
    while True:
        start_pos = llm_params.find(start_marker, pos)
        if start_pos == -1:
            break

        if start_pos > 0 and llm_params[start_pos - 1] == '\\':
            pos = start_pos + len(start_marker)
            continue

        paren_depth = 0
        i = start_pos + len(start_marker)
        end_pos = -1
        while i < len(llm_params) - 1:
            if llm_params[i] == '(':
                paren_depth += 1
            elif llm_params[i] == ')':
                paren_depth -= 1
            elif llm_params[i] == '}' and llm_params[i + 1] == '}' and paren_depth == 0:
                end_pos = i
                break
            i += 1

        if end_pos == -1:
            break

        url_content = llm_params[start_pos + len(start_marker):end_pos]

        xpath = None
        xpath_start = url_content.find('(')
        if xpath_start != -1:
            xpath_end = url_content.find(')', xpath_start)
            if xpath_end != -1:
                xpath = url_content[xpath_start + 1:xpath_end]
                url_content = url_content[:xpath_start] + url_content[xpath_end + 1:]

        url_content = url_content.rstrip('/')
        parts = url_content.split('/')

        if len(parts) < 2 or parts[0] != 'document':
            pos = end_pos + 1
            continue

        try:
            doc_id = int(parts[1])
        except (ValueError, IndexError):
            pos = end_pos + 1
            continue

        page_num = None
        ext_id = None

        i = 2
        while i < len(parts):
            if parts[i] == 'page' and i + 1 < len(parts):
                try:
                    page_num = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif parts[i] == 'extraction' and i + 1 < len(parts):
                try:
                    ext_id = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1

        references.append(
            ParsedReference(
                document_id=doc_id,
                page_number=page_num,
                extraction_id=ext_id,
                xpath=xpath,
            )
        )

        pos = end_pos + 2

    return references


def validate_and_normalize_references(
    user: User, references: list[ParsedReference]
) -> list[ParsedReference]:
    validated = []
    seen_keys = set()

    for ref in references:
        try:
            validate_reference(user, ref)

            if ref.xpath:
                key = (ref.document_id, ref.extraction_id, ref.page_number, ref.xpath)
            elif ref.extraction_id:
                key = (ref.document_id, ref.extraction_id, ref.page_number)
            elif ref.page_number:
                key = (ref.document_id, ref.page_number)
            else:
                key = (ref.document_id,)

            if key not in seen_keys:
                seen_keys.add(key)
                validated.append(ref)

        except Exception as e:
            logger.warning(
                "Skipping invalid reference for document %s (extraction: %s, page: %s, xpath: %s): %s",
                ref.document_id,
                ref.extraction_id,
                ref.page_number,
                ref.xpath,
                str(e),
            )
            continue

    return validated


def validate_reference(user: User, ref: ParsedReference) -> None:
    doc = validate_document_access(user, ref.document_id)

    if ref.extraction_id:
        ext = validate_extraction_access(user, ref.extraction_id, doc)

        if ref.page_number:
            validate_extraction_page_exists(ext, ref.page_number)

            if ref.xpath:
                validate_xpath(ext, ref.page_number, ref.xpath)
    elif ref.page_number:
        validate_document_page_exists(doc, ref.page_number)


def validate_document_access(user: User, document_id: int) -> document.Document:
    try:
        doc = document.Document.objects.get(id=document_id)
    except document.Document.DoesNotExist as e:
        raise ValueError(f"Document {document_id} not found") from e

    if doc.uploaded_by != user and not user.has_perm(
        "badgerdoc.view_other_users_document"
    ):
        raise ValueError(f"No access to document {document_id}")

    return doc


def validate_extraction_access(
    user: User, extraction_id: int, doc: document.Document
) -> extraction.Extraction:
    try:
        ext = extraction.Extraction.objects.get(id=extraction_id)
    except extraction.Extraction.DoesNotExist as e:
        raise ValueError(f"Extraction {extraction_id} not found") from e

    if ext.document_id != doc.id:
        raise ValueError(
            f"Extraction {extraction_id} does not belong to document {doc.id}"
        )

    if ext.created_by != user and not user.has_perm(
        "badgerdoc.view_other_users_extractions"
    ):
        raise ValueError(f"No access to extraction {extraction_id}")

    return ext


def validate_extraction_page_exists(
    ext: extraction.Extraction, page_number: int
) -> None:
    if not extraction_page.ExtractionPage.objects.filter(
        extraction=ext, page_number=page_number
    ).exists():
        raise ValueError(
            f"Page {page_number} not found in extraction {ext.id}"
        )


def validate_document_page_exists(
    doc: document.Document, page_number: int
) -> None:
    has_page = document.Document.objects.filter(
        parent_document=doc,
        tags__contains=["rendition"],
        metadata__page=page_number,
    ).exists()

    if not has_page:
        raise ValueError(f"Page {page_number} not found in document {doc.id}")


def validate_xpath(
    ext: extraction.Extraction, page_number: int, xpath: str
) -> None:
    try:
        page = extraction_page.ExtractionPage.objects.get(
            extraction=ext, page_number=page_number
        )
    except extraction_page.ExtractionPage.DoesNotExist as e:
        raise ValueError(
            f"Page {page_number} not found in extraction {ext.id}"
        ) from e

    if not page.content:
        raise ValueError(f"Page {page_number} has no content")

    try:
        tree = etree.HTML(page.content.encode("utf-8"))
        nodes = tree.xpath(xpath)
        if not nodes:
            raise ValueError(
                f"XPath '{xpath}' does not match any nodes on page {page_number}"
            )
    except etree.XPathEvalError as e:
        raise ValueError(f"Invalid XPath expression: {xpath}") from e
    except Exception as e:
        raise ValueError(f"Error evaluating XPath: {str(e)}") from e


def collect_documents(
    references: list[ParsedReference],
) -> list[document.Document]:
    doc_ids = set()
    for ref in references:
        if not ref.extraction_id and not ref.page_number:
            doc_ids.add(ref.document_id)

    if not doc_ids:
        return []

    return list(document.Document.objects.filter(id__in=doc_ids))


def collect_extractions(
    references: list[ParsedReference],
) -> list[extraction.Extraction]:
    ext_ids = {ref.extraction_id for ref in references if ref.extraction_id and not ref.page_number}

    if not ext_ids:
        return []

    return list(extraction.Extraction.objects.filter(id__in=ext_ids))


def collect_extraction_pages(
    references: list[ParsedReference],
) -> list[extraction_page.ExtractionPage]:
    page_keys = set()
    for ref in references:
        if ref.extraction_id and ref.page_number and not ref.xpath:
            page_keys.add((ref.extraction_id, ref.page_number))

    if not page_keys:
        return []

    pages = []
    for ext_id, page_num in page_keys:
        try:
            page = extraction_page.ExtractionPage.objects.get(
                extraction_id=ext_id, page_number=page_num
            )
            pages.append(page)
        except extraction_page.ExtractionPage.DoesNotExist:
            logger.warning(
                "Extraction page not found: extraction_id=%s, page_number=%s",
                ext_id,
                page_num,
            )

    return pages


def collect_xpaths(
    references: list[ParsedReference],
) -> list[extraction_helpers.BadgerdocExtractionXpath]:
    xpath_refs = []
    seen = set()

    for ref in references:
        if ref.extraction_id and ref.page_number and ref.xpath:
            key = (ref.extraction_id, ref.page_number, ref.xpath)
            if key not in seen:
                seen.add(key)
                try:
                    page = extraction_page.ExtractionPage.objects.get(
                        extraction_id=ref.extraction_id, page_number=ref.page_number
                    )
                    xpath_refs.append(
                        extraction_helpers.BadgerdocExtractionXpath(
                            extraction_page=page,
                            xpath=ref.xpath,
                        )
                    )
                except extraction_page.ExtractionPage.DoesNotExist:
                    logger.warning(
                        "Extraction page not found for xpath: extraction_id=%s, page_number=%s",
                        ref.extraction_id,
                        ref.page_number,
                    )

    return xpath_refs
