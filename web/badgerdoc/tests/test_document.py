import json
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from badgerdoc.models import document, workflow_registry
from badgerdoc.tests.settings import mock_db_and_file_storage


@mock_db_and_file_storage
@override_settings(
    BADGERDOC_LIFECYCLE_WORKFLOW_TYPE="TestWorkflow",
    BADGERDOC_LIFECYCLE_QUEUE="test-queue",
)
class DocumentParentDocumentTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@test.com", password="testpass123"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
        )
        self.permission_user = User.objects.create_user(
            username="permission_user",
            email="permission@test.com",
            password="testpass123",
        )
        permission = Permission.objects.get(
            codename="view_other_users_document"
        )
        self.permission_user.user_permissions.add(permission)

        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()
        patch(
            "badgerdoc.signals.workflow.get_supported_workflows",
            return_value=["workflow name"],
        ).start()

        workflow_registry.WorkflowRegistry.objects.create(
            created_by=self.owner,
            event_entity="document",
            event_type="on_create",
            document_types=["txt"],
            entity_tags=[],
            temporal_workflow_type="TestWorkflow",
            temporal_queue="test-queue",
            is_active=True,
            trigger="automatic",
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def test_upload_document_without_parent(self):
        self.client.force_authenticate(user=self.owner)

        file_content = b"test content"
        file = BytesIO(file_content)
        file.name = "test.txt"

        response = self.client.post(
            "/badgerdoc/document/",
            {"file": file, "extension": "txt"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["parent_document_id"])
        self.assertEqual(response.data["extension"], "txt")

    def test_upload_document_triggers_temporal_workflow(self):
        self.client.force_authenticate(user=self.owner)

        file_content = b"test content"
        file = BytesIO(file_content)
        file.name = "test.txt"

        self.client.post(
            "/badgerdoc/document/",
            {"file": file, "extension": "txt"},
            format="multipart",
        )

        self.assertTrue(self.mock_trigger_workflow.called)

    def test_upload_document_with_parent(self):
        self.client.force_authenticate(user=self.owner)
        parent_document = document.Document.objects.create(
            file="parent.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )
        file_content = b"test content"
        file = BytesIO(file_content)
        file.name = "child.txt"

        response = self.client.post(
            "/badgerdoc/document/",
            {
                "file": file,
                "parent_document_id": parent_document.id,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["parent_document_id"], parent_document.id
        )

    def test_upload_document_with_parent_not_owned_fails(self):
        self.client.force_authenticate(user=self.owner)
        parent_document = document.Document.objects.create(
            file="parent.pdf",
            uploaded_by=self.other_user,
            extension="pdf",
        )

        file_content = b"test content"
        file = BytesIO(file_content)
        file.name = "child.txt"

        response = self.client.post(
            "/badgerdoc/document/",
            {
                "file": file,
                "parent_document_id": parent_document.id,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_document_includes_extension(self):
        self.client.force_authenticate(user=self.owner)
        document_ = document.Document.objects.create(
            file="test_document.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )

        response = self.client.get(f"/badgerdoc/document/{document_.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["extension"], "pdf")

    def test_get_document_includes_parent_document_id(self):
        self.client.force_authenticate(user=self.owner)

        parent_document = document.Document.objects.create(
            file="parent.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )
        child_document = document.Document.objects.create(
            file="child.txt",
            extension="txt",
            uploaded_by=self.owner,
            parent_document=parent_document,
        )

        response = self.client.get(f"/badgerdoc/document/{child_document.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["parent_document_id"], parent_document.id
        )

    def test_list_documents_filter_by_parent_document_id(self):
        self.client.force_authenticate(user=self.owner)
        parent_document = document.Document.objects.create(
            file="parent.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )
        child_document1 = document.Document.objects.create(
            file="child1.txt",
            extension="txt",
            uploaded_by=self.owner,
            parent_document=parent_document,
        )
        child_document2 = document.Document.objects.create(
            file="child2.txt",
            extension="txt",
            uploaded_by=self.owner,
            parent_document=parent_document,
        )
        document.Document.objects.create(
            file="other.txt",
            uploaded_by=self.owner,
            extension="txt",
        )

        list_response = self.client.get(
            f"/badgerdoc/documents/?parent_document_id={parent_document.id}"
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 2)
        returned_ids = {doc["id"] for doc in list_response.data["results"]}
        self.assertEqual(
            returned_ids, {child_document1.id, child_document2.id}
        )

    def test_document_extension_property(self):
        document1 = document.Document.objects.create(
            file="test_document.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )
        self.assertEqual(document1.extension, "pdf")

        document2 = document.Document.objects.create(
            file="test_document.tar.gz",
            uploaded_by=self.owner,
            extension="gz",
        )
        self.assertEqual(document2.extension, "gz")

        document3 = document.Document.objects.create(
            file="no_extension",
            uploaded_by=self.owner,
        )
        self.assertEqual(document3.extension, None)

    def test_owner_can_view_own_document(self):
        self.client.force_authenticate(user=self.owner)
        document_ = document.Document.objects.create(
            file="test.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )

        response = self.client.get(f"/badgerdoc/document/{document_.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_owner_cannot_view_document(self):
        self.client.force_authenticate(user=self.other_user)
        document_ = document.Document.objects.create(
            file="test.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )

        response = self.client.get(f"/badgerdoc/document/{document_.id}/")

        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_view_any_document(self):
        self.client.force_authenticate(user=self.admin_user)
        document_ = document.Document.objects.create(
            file="test.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )

        response = self.client.get(f"/badgerdoc/document/{document_.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_with_permission_can_view_any_document(self):
        self.client.force_authenticate(user=self.permission_user)
        document_ = document.Document.objects.create(
            file="test.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )

        response = self.client.get(f"/badgerdoc/document/{document_.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_documents_respects_permissions(self):
        self.client.force_authenticate(user=self.owner)
        owner_document = document.Document.objects.create(
            file="owner.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )
        document.Document.objects.create(
            file="other.pdf",
            uploaded_by=self.other_user,
            extension="pdf",
        )

        list_response = self.client.get("/badgerdoc/documents/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(
            list_response.data["results"][0]["id"], owner_document.id
        )

    def test_admin_list_documents_sees_all(self):
        self.client.force_authenticate(user=self.admin_user)
        document.Document.objects.create(
            file="owner.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )
        document.Document.objects.create(
            file="other.pdf",
            uploaded_by=self.other_user,
            extension="pdf",
        )

        list_response = self.client.get("/badgerdoc/documents/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 2)

    def test_create_with_file_and_reupload(self):
        self.client.force_authenticate(user=self.owner)

        file_content = b"original"
        file = BytesIO(file_content)
        file.name = "orig.txt"

        response = self.client.post(
            "/badgerdoc/document/",
            {"file": file, "extension": "txt"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.data["id"]
        self.assertEqual(response.data["extension"], "txt")

        new_file = BytesIO(b"updated")
        new_file.name = "updated.md"

        patch_resp = self.client.patch(
            f"/badgerdoc/document/{doc_id}/",
            {"file": new_file, "extension": "md"},
            format="multipart",
        )

        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data["extension"], "md")

    def test_create_without_file_then_upload_later(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/badgerdoc/document/",
            {},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.data["id"]
        self.assertIsNone(response.data.get("extension"))

        file = BytesIO(b"late content")
        file.name = "late.pdf"

        patch_resp = self.client.patch(
            f"/badgerdoc/document/{doc_id}/",
            {"file": file, "extension": "pdf"},
            format="multipart",
        )

        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data["extension"], "pdf")

    def test_update_document_metadata(self):
        self.client.force_authenticate(user=self.owner)

        file = BytesIO(b"meta")
        file.name = "meta.txt"

        response = self.client.post(
            "/badgerdoc/document/",
            {"file": file, "extension": "txt"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.data["id"]

        metadata = {"key": "value", "num": 1}
        patch_resp = self.client.patch(
            f"/badgerdoc/document/{doc_id}/",
            {"metadata": json.dumps(metadata)},
            format="multipart",
        )

        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data["metadata"], metadata)

    def test_create_with_all_fields(self):
        self.client.force_authenticate(user=self.owner)

        parent_doc = document.Document.objects.create(
            file="parent.pdf",
            uploaded_by=self.owner,
            extension="pdf",
        )

        file = BytesIO(b"all")
        file.name = "all.txt"

        payload = {
            "file": file,
            "parent_document_id": parent_doc.id,
            "metadata": json.dumps({"a": 1}),
            "tags": json.dumps(["t1", "t2"]),
            "extension": "txt",
        }

        response = self.client.post(
            "/badgerdoc/document/",
            payload,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["parent_document_id"], parent_doc.id)
        self.assertEqual(response.data["extension"], "txt")
        self.assertEqual(response.data["metadata"], {"a": 1})
        self.assertEqual(response.data["tags"], ["t1", "t2"])

    def test_field_validations(self):
        self.client.force_authenticate(user=self.owner)

        file = BytesIO(b"x")
        file.name = "x.txt"

        resp = self.client.post(
            "/badgerdoc/document/",
            {"file": file, "tags": "not-a-list", "extension": "txt"},
            format="multipart",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp2 = self.client.post(
            "/badgerdoc/document/",
            {"metadata": "{invalid:}", "extension": "txt"},
            format="multipart",
        )

        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_documents_metadata_filter_simple_value(self):
        self.client.force_authenticate(user=self.owner)

        doc1 = document.Document.objects.create(
            file="meta1.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"type": "article"},
        )
        document.Document.objects.create(
            file="meta2.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"type": "report"},
        )

        resp = self.client.get(
            "/badgerdoc/documents/",
            {"metadata": json.dumps({"type": "article"})},
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["id"], doc1.id)

    def test_list_documents_metadata_filter_list_or(self):
        self.client.force_authenticate(user=self.owner)

        d1 = document.Document.objects.create(
            file="s1.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"source": "elsevier"},
        )
        d2 = document.Document.objects.create(
            file="s2.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"source": "epo ops"},
        )
        document.Document.objects.create(
            file="s3.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"source": "google patents"},
        )

        resp = self.client.get(
            "/badgerdoc/documents/",
            {"metadata": json.dumps({"source": ["elsevier", "epo ops"]})},
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)
        returned_ids = {doc["id"] for doc in resp.data["results"]}
        self.assertEqual(returned_ids, {d1.id, d2.id})

    def test_list_documents_metadata_filter_with_lookup_and_combined_fields(
        self,
    ):
        self.client.force_authenticate(user=self.owner)

        doc_a = document.Document.objects.create(
            file="a.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"type": "article", "source": "elsevier"},
        )
        document.Document.objects.create(
            file="b.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"type": "article", "source": "epo ops"},
        )
        document.Document.objects.create(
            file="c.pdf",
            uploaded_by=self.owner,
            extension="pdf",
            metadata={"type": "report", "source": "elsevier"},
        )

        filter_payload = {"type": "article", "source": ["elsevier"]}
        resp = self.client.get(
            "/badgerdoc/documents/", {"metadata": json.dumps(filter_payload)}
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["id"], doc_a.id)
