from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from badgerdoc.models import (
    document,
    extraction,
    extraction_document,
)
from badgerdoc.tests.settings import mock_db_and_file_storage


@mock_db_and_file_storage
class ExtractionDocumentAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="pass"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@test.com", password="pass"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="pass",
            is_staff=True,
        )
        self.permission_user = User.objects.create_user(
            username="permission_user",
            email="permission@test.com",
            password="pass",
        )
        self.permission_user.user_permissions.add(
            Permission.objects.get(codename="view_other_users_extractions")
        )

        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()

        file_content = b"test document content"
        file = SimpleUploadedFile(
            "test_doc.txt", file_content, content_type="text/plain"
        )
        self.document = document.Document.objects.create(
            file=file, uploaded_by=self.owner
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def _url(self, extraction_id: int) -> str:
        return f"/badgerdoc/extraction/{extraction_id}/extraction-document/"

    def test_create_extraction_document_happy_path(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        response = self.client.post(
            self._url(ext.id), {"content": {"data": "ok"}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["extraction_id"], ext.id)
        self.assertEqual(response.data["content"], {"data": "ok"})

        self.assertTrue(
            extraction_document.ExtractionDocument.objects.filter(
                extraction=ext
            ).exists()
        )

    def test_create_extraction_document_bad_content(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        response = self.client.post(
            self._url(ext.id), {"content": None}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_extraction_document_nonexistent_extraction(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            self._url(99), {"content": {"x": 1}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_extraction_document_when_extraction_terminated(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        response = self.client.post(
            self._url(ext.id), {"content": {"x": 1}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stopped", response.data.get("error", ""))

    def test_create_extraction_document_by_non_creator_fails(self):
        self.client.force_authenticate(user=self.other_user)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        response = self.client.post(
            self._url(ext.id), {"content": {"x": 1}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_extraction_document_happy_path(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )
        extraction_document.ExtractionDocument.objects.create(
            extraction=ext, content={"data": "old"}
        )

        response = self.client.patch(
            self._url(ext.id), {"content": {"data": "new"}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], {"data": "new"})

    def test_update_extraction_document_without_existing_document(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        response = self.client.patch(
            self._url(ext.id), {"content": {"x": 1}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_extraction_document_bad_content(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )
        extraction_document.ExtractionDocument.objects.create(
            extraction=ext, content={"data": "old"}
        )

        response = self.client.patch(
            self._url(ext.id), {"content": None}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_extraction_document_nonexistent_extraction(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            self._url(99), {"content": {"x": 1}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_extraction_document_when_extraction_terminated(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_document.ExtractionDocument.objects.create(
            extraction=ext, content={"data": "old"}
        )

        response = self.client.patch(
            self._url(ext.id), {"content": {"x": 1}}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_extraction_document_happy_path(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )
        extraction_document.ExtractionDocument.objects.create(
            extraction=ext, content={"data": "ok"}
        )

        response = self.client.get(self._url(ext.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], {"data": "ok"})

    def test_get_extraction_document_missing_document(self):
        self.client.force_authenticate(user=self.owner)

        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        response = self.client.get(self._url(ext.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_extraction_document_nonexistent_extraction(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(self._url(99))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_extraction_document_permission_checks(self):
        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )
        extraction_document.ExtractionDocument.objects.create(
            extraction=ext, content={"data": "ok"}
        )

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self._url(ext.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._url(ext.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.permission_user)
        response = self.client.get(self._url(ext.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_access(self):
        ext = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        response = self.client.get(self._url(ext.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
