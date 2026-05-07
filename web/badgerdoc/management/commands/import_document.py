"""
Script for automated setup of test data from ZIP archives.

This command processes a ZIP archive containing folders with JSON metadata and files,
automatically creating documents, extractions, extraction pages, and tasks.
Supports document hierarchies and relational data.

Usage:
    python manage.py import_document /path/to/export.zip
"""

import json
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_save

from badgerdoc.models import (
    document,
    extraction,
    extraction_document,
    extraction_page,
    task,
    task_extraction,
    task_status,
)
from badgerdoc.signals import trigger_automatic

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Automatically setup test data from a ZIP archive (relational)"

    def add_arguments(self, parser):
        parser.add_argument(
            "zip_path",
            type=str,
            help="Path to the ZIP archive containing test data",
        )
        parser.add_argument(
            "--username",
            type=str,
            default=os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin"),
            help="Username to create entities as (default: admin)",
        )

    def handle(self, *args, **options):
        zip_path = options["zip_path"]
        username = options["username"]
        if not os.path.exists(zip_path):
            raise CommandError(f"ZIP file not found: {zip_path}")

        try:
            admin_user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"Using user: {admin_user.username}"))
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found.")

        self.stdout.write(f"Processing ZIP archive: {zip_path}")

        # Disconnect signals to prevent triggering workflows during import
        self.stdout.write("Disconnecting automatic workflow signals...")
        post_save.disconnect(receiver=trigger_automatic.handle_document_save, sender=document.Document)
        post_save.disconnect(receiver=trigger_automatic.handle_extraction_save, sender=extraction.Extraction)
        post_save.disconnect(receiver=trigger_automatic.handle_task_save, sender=task.Task)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                try:
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(temp_path)
                except zipfile.BadZipFile:
                    raise CommandError(f"Invalid ZIP file: {zip_path}")

                metadata_files = list(temp_path.rglob("metadata.json"))
                if not metadata_files:
                    raise CommandError("No metadata.json files found in ZIP archive")

                self.stdout.write(f"Found {len(metadata_files)} document records to process\n")

                # Two-pass processing
                doc_mapping = {}  # original_id -> new_Document_instance
                ext_mapping = {}  # original_id -> new_Extraction_instance

                self._create_documents(metadata_files, admin_user, doc_mapping)
                self._create_relations(metadata_files, doc_mapping, ext_mapping, admin_user)
        finally:
            # Reconnect signals
            self.stdout.write("Reconnecting automatic workflow signals...")
            post_save.connect(receiver=trigger_automatic.handle_document_save, sender=document.Document)
            post_save.connect(receiver=trigger_automatic.handle_extraction_save, sender=extraction.Extraction)
            post_save.connect(receiver=trigger_automatic.handle_task_save, sender=task.Task)

        self.stdout.write(self.style.SUCCESS("\nImport completed successfully."))

    def _create_documents(self, metadata_files: list[Path], admin_user: Any, doc_mapping: dict[int, Any]):
        """First pass: Create Document objects."""
        with transaction.atomic():
            for metadata_file in metadata_files:
                try:
                    folder_path = metadata_file.parent
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                    doc = self._create_document(metadata, folder_path, admin_user)
                    doc_mapping[metadata["id"]] = doc
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Document {metadata['id']} created as {doc.id}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Failed Pass 1 for {metadata_file}: {e}"))
                    raise e

    def _create_relations(
        self,
        metadata_files: list[Path],
        doc_mapping: dict[int, Any],
        ext_mapping: dict[int, Any],
        admin_user: Any
    ):
        """Second pass: Restore relationships and related data."""
        with transaction.atomic():
            for metadata_file in metadata_files:
                try:
                    folder_path = metadata_file.parent
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                    doc = doc_mapping[metadata["id"]]
                    self._restore_relationships(doc, metadata, doc_mapping, ext_mapping, folder_path, admin_user)

                    self.stdout.write(self.style.SUCCESS(f"  ✓ Relationships restored for doc {doc.id}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Failed Pass 2 for Record {metadata['id']}: {e}"))
                    raise e

    def _restore_relationships(
        self,
        doc: Any,
        metadata: dict,
        doc_mapping: dict[int, Any],
        ext_mapping: dict[int, Any],
        folder_path: Path,
        admin_user: Any
    ):
        """Helper to restore all relationships for a single document."""
        # Parent relationship
        old_parent_id = metadata["document"].get("parent_id")
        if old_parent_id and old_parent_id in doc_mapping:
            doc.parent_document = doc_mapping[old_parent_id]
            doc.save()

        # Extractions
        for ext_data in metadata.get("extractions", []):
            new_ext = self._create_extraction(ext_data, folder_path, doc, admin_user)
            ext_mapping[ext_data["id"]] = new_ext

        # Pass 2 of relations: Tasks (link to extractions)
        for task_data in metadata.get("tasks", []):
            self._create_task(task_data, doc, admin_user, ext_mapping)

    def _create_document(self, metadata: dict, folder_path: Path, admin_user: Any) -> document.Document:
        doc_config = metadata["document"]
        doc = document.Document(
            name=doc_config.get("name"),
            uploaded_by=admin_user,
            extension=doc_config.get("extension"),
            tags=doc_config.get("tags", []),
            metadata=doc_config.get("metadata", {}),
        )

        filename = doc_config.get("filename")
        if filename:
            file_path = folder_path / filename
            if file_path.exists():
                with open(file_path, "rb") as f:
                    doc.file.save(filename, ContentFile(f.read()), save=False)
        
        doc.save()
        return doc

    def _create_extraction(self, ext_data: dict, folder_path: Path, doc: document.Document, admin_user: Any) -> extraction.Extraction:
        # Avoid doubling pages if we are re-importing over existing data (unlikely in fresh setup but good for idempotency)
        ext = extraction.Extraction.objects.create(
            document=doc,
            created_by=admin_user,
            status=ext_data.get("status", extraction.ExtractionStatus.COMPLETED),
            comment=ext_data.get("comment", ""),
            tags=ext_data.get("tags", []),
        )

        # ExtractionDocument (JSON)
        if ext_data.get("content"):
            extraction_document.ExtractionDocument.objects.update_or_create(
                extraction=ext,
                defaults={"content": ext_data["content"]}
            )

        # ExtractionPages (hOCR)
        for page_config in ext_data.get("pages", []):
            content_file = folder_path / page_config["content_file"]
            with open(content_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            extraction_page.ExtractionPage.objects.update_or_create(
                extraction=ext,
                page_number=page_config["page_number"],
                defaults={"content": content}
            )

        return ext

    def _create_task(self, task_data: dict, doc: document.Document, admin_user: Any, ext_mapping: dict):
        status_name = task_data.get("status_name")
        status_obj = task_status.TaskStatus.objects.filter(name=status_name).first()
        if not status_obj:
            status_obj = task_status.TaskStatus.objects.order_by("order").first()

        new_task = task.Task.objects.create(
            user=admin_user,
            document=doc,
            status=status_obj,
            tags=task_data.get("tags", []),
        )

        for old_ext_id in task_data.get("extraction_ids", []):
            if old_ext_id in ext_mapping:
                task_extraction.TaskExtraction.objects.create(
                    task=new_task,
                    extraction=ext_mapping[old_ext_id]
                )
