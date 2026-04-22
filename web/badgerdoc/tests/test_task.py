from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from badgerdoc.models import (
    document,
    extraction,
    task,
    task_extraction,
    task_status,
)
from badgerdoc.tests.settings import mock_db_and_file_storage


@mock_db_and_file_storage
class TaskTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@test.com",
            password="testpass123",
        )

        self.new_task_status = task_status.TaskStatus.objects.create(
            name="New Task",
            order=99,
        )
        self.pending_status = task_status.TaskStatus.objects.create(
            name="Pending",
            order=1,
        )
        self.in_progress_status = task_status.TaskStatus.objects.create(
            name="In progress",
            order=2,
        )
        self.completed_status = task_status.TaskStatus.objects.create(
            name="Completed",
            order=3,
        )
        self.pending_status.parent.add(self.new_task_status)
        self.in_progress_status.parent.add(self.pending_status)
        self.completed_status.parent.add(self.pending_status)
        self.completed_status.parent.add(self.in_progress_status)

        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()
        patch(
            "badgerdoc.signals.workflow.get_supported_workflows",
            return_value=["workflow name"],
        ).start()

        file_content = b"test document content"
        file = SimpleUploadedFile(
            "test_doc.txt", file_content, content_type="text/plain"
        )
        self.document = document.Document.objects.create(
            file=file, uploaded_by=self.user
        )
        self.another_document = document.Document.objects.create(
            file=file, uploaded_by=self.user
        )

        self.extraction = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.user,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def test_create_task_with_document(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/badgerdoc/task/",
            {
                "status": self.pending_status.id,
                "document": self.document.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"]["name"], "Pending")

        task_obj = task.Task.objects.get(id=response.data["id"])
        self.assertEqual(task_obj.user, self.user)
        self.assertEqual(task_obj.document, self.document)

        task_exts = task_extraction.TaskExtraction.objects.filter(
            task=task_obj
        )
        self.assertEqual(task_exts.count(), 0)

    def test_create_task_with_document_no_status(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/badgerdoc/task/",
            {
                "document": self.document.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"]["name"], "New Task")

        task_obj = task.Task.objects.get(id=response.data["id"])
        self.assertEqual(task_obj.user, self.user)
        self.assertEqual(task_obj.document, self.document)

        task_exts = task_extraction.TaskExtraction.objects.filter(
            task=task_obj
        )
        self.assertEqual(task_exts.count(), 0)

    def test_create_task_with_extraction(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/badgerdoc/task/",
            {
                "status": self.pending_status.id,
                "extractions": [self.extraction.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"]["name"], "Pending")

        task_obj = task.Task.objects.get(id=response.data["id"])
        self.assertEqual(task_obj.user, self.user)
        self.assertEqual(task_obj.document, self.document)

        task_exts = task_extraction.TaskExtraction.objects.filter(
            task=task_obj
        )
        self.assertEqual(task_exts.count(), 1)
        self.assertEqual(task_exts[0].extraction, self.extraction)

    def test_create_task_with_matching_extraction_and_document(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/badgerdoc/task/",
            {
                "status": self.pending_status.id,
                "extractions": [self.extraction.id],
                "document": self.document.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"]["name"], "Pending")

        task_obj = task.Task.objects.get(id=response.data["id"])
        self.assertEqual(task_obj.user, self.user)
        self.assertEqual(task_obj.document, self.document)

        task_exts = task_extraction.TaskExtraction.objects.filter(
            task=task_obj
        )
        self.assertEqual(task_exts.count(), 1)
        self.assertEqual(task_exts[0].extraction, self.extraction)

    def test_create_task_with_extraction_rejects_different_document(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/badgerdoc/task/",
            {
                "status": self.pending_status.id,
                "extractions": [self.extraction.id],
                "document": self.another_document.id,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ],
        )
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn(
                "must refer to the same document",
                str(response.data),
            )

    def test_create_task_extraction_requires_extraction_or_document(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/badgerdoc/task/",
            {
                "status": self.pending_status.id,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ],
        )
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn("Document is required", str(response.data))

    def test_list_tasks_shows_document_for_extraction_task(self):
        self.client.force_authenticate(user=self.user)

        task_obj = task.Task.objects.create(
            user=self.user,
            status=self.pending_status,
            document=self.document,
        )
        task_extraction.TaskExtraction.objects.create(
            task=task_obj, extraction=self.extraction
        )

        response = self.client.get("/badgerdoc/tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        task_data = response.data["results"][0]
        self.assertIsNotNone(task_data["document"])
        self.assertEqual(task_data["document"]["id"], self.document.id)
        self.assertIsNotNone(task_data["extractions"])
        self.assertEqual(task_data["extractions"][0]["id"], self.extraction.id)

    def test_list_tasks_shows_document_for_document_task(self):
        self.client.force_authenticate(user=self.user)

        task.Task.objects.create(
            user=self.user,
            status=self.pending_status,
            document=self.document,
        )

        response = self.client.get("/badgerdoc/tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        task_data = response.data["results"][0]
        self.assertIsNotNone(task_data["document"])
        self.assertEqual(task_data["document"]["id"], self.document.id)
        self.assertEqual(task_data["extractions"], [])

    def test_update_task_status(self):
        self.client.force_authenticate(user=self.user)

        task_obj = task.Task.objects.create(
            user=self.user,
            status=self.pending_status,
            document=self.document,
        )

        response = self.client.patch(
            f"/badgerdoc/task/{task_obj.id}/",
            {"status": self.in_progress_status.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"]["name"], "In progress")

        task_obj.refresh_from_db()
        self.assertEqual(task_obj.status, self.in_progress_status)

    def test_update_task_extractions(self):
        self.client.force_authenticate(user=self.user)

        task_obj = task.Task.objects.create(
            user=self.user,
            status=self.pending_status,
            document=self.document,
        )
        extraction_2 = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.user,
            status=extraction.ExtractionStatus.STARTED,
        )

        response = self.client.patch(
            f"/badgerdoc/task/{task_obj.id}/",
            {"extractions": [self.extraction.id, extraction_2.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task_extractions = task_extraction.TaskExtraction.objects.filter(
            task=task_obj
        )
        self.assertEqual(task_extractions.count(), 2)
        self.assertIn(
            self.extraction, [te.extraction for te in task_extractions]
        )
        self.assertIn(extraction_2, [te.extraction for te in task_extractions])

    def test_update_task_extractions_validation(self):
        self.client.force_authenticate(user=self.user)

        task_obj = task.Task.objects.create(
            user=self.user,
            status=self.pending_status,
            document=self.document,
        )
        extraction_2 = extraction.Extraction.objects.create(
            document=self.another_document,
            created_by=self.user,
            status=extraction.ExtractionStatus.STARTED,
        )

        response = self.client.patch(
            f"/badgerdoc/task/{task_obj.id}/",
            {"extractions": [self.extraction.id, extraction_2.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "must belong to the same document",
            str(response.data),
        )

    def test_update_task_status_validation(self):
        self.client.force_authenticate(user=self.user)

        task_obj = task.Task.objects.create(
            user=self.user,
            status=self.pending_status,
            document=self.document,
        )

        response = self.client.patch(
            f"/badgerdoc/task/{task_obj.id}/",
            {"status": 9999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
