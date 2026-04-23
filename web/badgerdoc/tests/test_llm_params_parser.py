from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase

from badgerdoc import llm_params_parser
from badgerdoc.models import document, extraction, extraction_page
from badgerdoc.tests.settings import mock_db_and_file_storage


class ExtractReferencesTestCase(TestCase):
    def test_whole_document(self):
        llm_params = "{{/badgerdoc/document/123/}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 123)
        self.assertIsNone(result[0].page_number)
        self.assertIsNone(result[0].extraction_id)
        self.assertIsNone(result[0].xpath)

    def test_single_page(self):
        llm_params = "{{/badgerdoc/document/123/page/1}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].page_number, 1)
        self.assertIsNone(result[0].extraction_id)
        self.assertIsNone(result[0].xpath)

    def test_multiple_pages(self):
        llm_params = "{{/badgerdoc/document/123/page/1}}{{/badgerdoc/document/123/page/2}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 2)

        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].page_number, 1)
        self.assertIsNone(result[0].extraction_id)
        self.assertIsNone(result[0].xpath)

        self.assertEqual(result[1].document_id, 123)
        self.assertEqual(result[1].page_number, 2)
        self.assertIsNone(result[1].extraction_id)
        self.assertIsNone(result[1].xpath)

    def test_extraction_page(self):
        llm_params = "{{/badgerdoc/document/123/extraction/456/page/1/}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].extraction_id, 456)
        self.assertEqual(result[0].page_number, 1)
        self.assertIsNone(result[0].xpath)

    def test_extraction_with_xpath(self):
        llm_params = "{{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].extraction_id, 456)
        self.assertEqual(result[0].page_number, 1)
        self.assertEqual(result[0].xpath, "//div[@id='block_1_1']")

    def test_extraction_with_custom_prompt(self):
        llm_params = "Extract tables from {{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].extraction_id, 456)
        self.assertEqual(result[0].page_number, 1)
        self.assertEqual(result[0].xpath, "//div[@id='block_1_1']")

    def test_mixed_context_with_custom_prompt(self):
        llm_params = "Analyze these sections: {{/badgerdoc/document/123/page/1}}{{/badgerdoc/document/123/extraction/456/page/2/(//div[@id='block_2_abc'])}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 2)

        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].page_number, 1)
        self.assertIsNone(result[0].extraction_id)
        self.assertIsNone(result[0].xpath)

        self.assertEqual(result[1].document_id, 123)
        self.assertEqual(result[1].extraction_id, 456)
        self.assertEqual(result[1].page_number, 2)
        self.assertEqual(result[1].xpath, "//div[@id='block_2_abc']")

    def test_complex_multi_reference_with_duplicates(self):
        llm_params = "Extract tables from {{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}} then extract from {{/badgerdoc/document/123/extraction/456/page/1/(//div[@id='block_1_1'])}} and compare with document {{/badgerdoc/document/123/}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 3)

        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].extraction_id, 456)
        self.assertEqual(result[0].page_number, 1)
        self.assertEqual(result[0].xpath, "//div[@id='block_1_1']")

        self.assertEqual(result[1].document_id, 123)
        self.assertEqual(result[1].extraction_id, 456)
        self.assertEqual(result[1].page_number, 1)
        self.assertEqual(result[1].xpath, "//div[@id='block_1_1']")

        self.assertEqual(result[2].document_id, 123)
        self.assertIsNone(result[2].page_number)
        self.assertIsNone(result[2].extraction_id)
        self.assertIsNone(result[2].xpath)

    def test_empty_string(self):
        llm_params = ""

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 0)

    def test_no_references(self):
        llm_params = "Extract all tables from the provided document"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 0)

    def test_malformed_reference_no_closing_bracket(self):
        llm_params = "{{/badgerdoc/document/123/page/1"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 0)

    def test_malformed_reference_invalid_document_id(self):
        llm_params = "{{/badgerdoc/document/abc/page/1}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 0)

    def test_malformed_reference_no_document_segment(self):
        llm_params = "{{/badgerdoc/page/1}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 0)

    def test_document_without_trailing_slash(self):
        llm_params = "{{/badgerdoc/document/123}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 123)
        self.assertIsNone(result[0].page_number)
        self.assertIsNone(result[0].extraction_id)

    def test_extraction_without_trailing_slash(self):
        llm_params = "{{/badgerdoc/document/123/extraction/456/page/1}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 123)
        self.assertEqual(result[0].extraction_id, 456)
        self.assertEqual(result[0].page_number, 1)
        self.assertIsNone(result[0].xpath)

    def test_escaped_link(self):
        llm_params = r"This is not a link: \{{/badgerdoc/document/123/}}"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 0)

    def test_escaped_and_normal_link(self):
        llm_params = r"This \{{/badgerdoc/document/123/}} is escaped but {{/badgerdoc/document/456/}} is not"

        result = llm_params_parser.extract_references(llm_params)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].document_id, 456)


@mock_db_and_file_storage
class ParseFunctionTestCase(TestCase):
    def setUp(self):
        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()

        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="pass"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass",
            is_staff=True,
        )
        self.admin_user.user_permissions.add(
            Permission.objects.get(codename="view_other_users_document")
        )
        self.admin_user.user_permissions.add(
            Permission.objects.get(codename="view_other_users_extractions")
        )

        self.doc = document.Document.objects.create(
            file=None, uploaded_by=self.owner
        )
        self.child_doc = document.Document.objects.create(
            file=None,
            uploaded_by=self.owner,
            parent_document=self.doc,
            tags=["rendition"],
            metadata={"page": 1},
        )

        self.extraction = extraction.Extraction.objects.create(
            document=self.doc, created_by=self.owner, status="Completed"
        )
        self.extraction_page = extraction_page.ExtractionPage.objects.create(
            extraction=self.extraction,
            page_number=1,
            content="<html><body><div id='block_1'>Test</div></body></html>",
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def test_parse_success_whole_document(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/}}}}"

        result = llm_params_parser.parse(self.owner.id, llm_params)

        self.assertEqual(len(result.linked_documents), 1)
        self.assertEqual(result.linked_documents[0].id, self.doc.id)
        self.assertIsNone(result.linked_extractions)
        self.assertIsNone(result.linked_extraction_pages)
        self.assertIsNone(result.linked_extraction_xpaths)
        self.assertEqual(result.prompt_text, llm_params)

    def test_parse_success_document_page(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/page/1}}}}"

        result = llm_params_parser.parse(self.owner.id, llm_params)

        self.assertEqual(len(result.linked_documents), 0)
        self.assertIsNone(result.linked_extractions)
        self.assertIsNone(result.linked_extraction_pages)
        self.assertIsNone(result.linked_extraction_xpaths)

    def test_parse_success_extraction_page(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/extraction/{self.extraction.id}/page/1/}}}}"

        result = llm_params_parser.parse(self.owner.id, llm_params)

        self.assertEqual(len(result.linked_documents), 0)
        self.assertIsNone(result.linked_extractions)
        self.assertEqual(len(result.linked_extraction_pages), 1)
        self.assertEqual(result.linked_extraction_pages[0].id, self.extraction_page.id)
        self.assertIsNone(result.linked_extraction_xpaths)

    def test_parse_success_xpath(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/extraction/{self.extraction.id}/page/1/(//div[@id='block_1'])}}}}"

        result = llm_params_parser.parse(self.owner.id, llm_params)

        self.assertEqual(len(result.linked_documents), 0)
        self.assertIsNone(result.linked_extractions)
        self.assertIsNone(result.linked_extraction_pages)
        self.assertEqual(len(result.linked_extraction_xpaths), 1)
        self.assertEqual(result.linked_extraction_xpaths[0].extraction_page.id, self.extraction_page.id)
        self.assertEqual(result.linked_extraction_xpaths[0].xpath, "//div[@id='block_1']")

    def test_parse_document_access_denied(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/}}}}"

        result = llm_params_parser.parse(self.other_user.id, llm_params)

        self.assertEqual(len(result.linked_documents), 0)
        self.assertIsNone(result.linked_extractions)
        self.assertIsNone(result.linked_extraction_pages)
        self.assertIsNone(result.linked_extraction_xpaths)

    def test_parse_document_access_granted_with_permission(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/}}}}"

        result = llm_params_parser.parse(self.admin_user.id, llm_params)

        self.assertEqual(len(result.linked_documents), 1)
        self.assertEqual(result.linked_documents[0].id, self.doc.id)

    def test_parse_extraction_access_denied(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/extraction/{self.extraction.id}/page/1/}}}}"

        result = llm_params_parser.parse(self.other_user.id, llm_params)

        self.assertEqual(len(result.linked_documents), 0)
        self.assertIsNone(result.linked_extractions)
        self.assertIsNone(result.linked_extraction_pages)
        self.assertIsNone(result.linked_extraction_xpaths)

    def test_parse_extraction_access_granted_with_permission(self):
        llm_params = f"{{{{/badgerdoc/document/{self.doc.id}/extraction/{self.extraction.id}/page/1/}}}}"

        result = llm_params_parser.parse(self.admin_user.id, llm_params)

        self.assertEqual(len(result.linked_documents), 0)
        self.assertIsNone(result.linked_extractions)
        self.assertEqual(len(result.linked_extraction_pages), 1)
        self.assertEqual(result.linked_extraction_pages[0].id, self.extraction_page.id)

    def test_parse_mixed_references(self):
        llm_params = f"Compare {{{{/badgerdoc/document/{self.doc.id}/}}}} with {{{{/badgerdoc/document/{self.doc.id}/extraction/{self.extraction.id}/page/1/}}}}"

        result = llm_params_parser.parse(self.owner.id, llm_params)

        self.assertEqual(len(result.linked_documents), 1)
        self.assertEqual(len(result.linked_extraction_pages), 1)
        self.assertEqual(result.prompt_text, llm_params)
