from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from badgerdoc.models import document, extraction
from badgerdoc.tests.settings import mock_db_and_file_storage


@mock_db_and_file_storage
class ExtractionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

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
        self.permission_user = User.objects.create_user(
            username="permission_user",
            email="permission@example.com",
            password="pass",
        )
        self.permission_user.user_permissions.add(
            Permission.objects.get(codename="view_other_users_extractions")
        )

        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()

        self.document = document.Document.objects.create(
            file=None, uploaded_by=self.owner
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def _create_extraction(self, **kwargs) -> extraction.Extraction:
        defaults = dict(document=self.document, created_by=self.owner)
        defaults.update(kwargs)
        return extraction.Extraction.objects.create(**defaults)

    def test_create_extraction_happy_path(self):
        self.client.force_authenticate(user=self.owner)

        data = {
            "document_id": self.document.id,
            "status": extraction.ExtractionStatus.STARTED,
            "comment": "ok",
            "tags": ["a"],
        }
        response = self.client.post(
            "/badgerdoc/extraction/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["document_id"], self.document.id)
        self.assertEqual(response.data["created_by"], str(self.owner))
        self.assertEqual(
            response.data["status"], extraction.ExtractionStatus.STARTED
        )

    def test_create_extraction_without_document_id(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/badgerdoc/extraction/",
            {"status": extraction.ExtractionStatus.STARTED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("document_id", response.data.get("error", ""))

    def test_create_extraction_with_nonexistent_document_id(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/badgerdoc/extraction/", {"document_id": 99}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Validation error", response.data.get("error", ""))

    def test_update_extraction_happy_path(self):
        self.client.force_authenticate(user=self.owner)

        extraction_ = self._create_extraction(
            status=extraction.ExtractionStatus.STARTED
        )

        response = self.client.patch(
            f"/badgerdoc/extraction/{extraction_.id}/",
            {
                "status": extraction.ExtractionStatus.COMPLETED,
                "comment": "done",
                "tags": ["x"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["status"], extraction.ExtractionStatus.COMPLETED
        )
        self.assertEqual(response.data["comment"], "done")
        self.assertEqual(response.data["tags"], ["x"])

    def test_update_extraction_not_allowed_fields_ignored(self):
        self.client.force_authenticate(user=self.owner)

        other_doc = document.Document.objects.create(
            file=None, uploaded_by=self.owner
        )
        extraction_ = self._create_extraction(
            status=extraction.ExtractionStatus.STARTED, temporal_job_id="orig"
        )

        response = self.client.patch(
            f"/badgerdoc/extraction/{extraction_.id}/",
            {
                "document_id": other_doc.id,
                "temporal_job_id": "new",
                "status": extraction.ExtractionStatus.IN_PROGRESS,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated = extraction.Extraction.objects.get(pk=extraction_.id)
        self.assertEqual(updated.document_id, self.document.id)
        self.assertEqual(updated.temporal_job_id, "orig")

    def test_update_extraction_with_nonexistent_status(self):
        self.client.force_authenticate(user=self.owner)

        extraction_ = self._create_extraction(
            status=extraction.ExtractionStatus.STARTED
        )
        response = self.client.patch(
            f"/badgerdoc/extraction/{extraction_.id}/",
            {"status": "Not Started"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Validation error", response.data.get("error", ""))

    def test_get_extraction_by_id(self):
        self.client.force_authenticate(user=self.owner)

        extraction_ = self._create_extraction(
            status=extraction.ExtractionStatus.STARTED
        )
        response = self.client.get(f"/badgerdoc/extraction/{extraction_.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], extraction_.id)

    def test_get_nonexistent_extraction(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get("/badgerdoc/extraction/99/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_extractions_permissions_and_pagination(self):
        self.client.force_authenticate(user=self.owner)
        self._create_extraction(status=extraction.ExtractionStatus.STARTED)
        extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.other_user,
            status=extraction.ExtractionStatus.STARTED,
        )

        response = self.client.get("/badgerdoc/extractions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results", [])), 1)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/badgerdoc/extractions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get("results", [])), 2)

        self.client.force_authenticate(user=self.permission_user)
        response = self.client.get("/badgerdoc/extractions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get("results", [])), 2)

    def test_unauthenticated_cannot_access(self):
        response = self.client.get("/badgerdoc/extractions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
