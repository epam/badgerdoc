"""
Script for exporting documents and their related data to a ZIP archive.

This command takes a list of document IDs, discovers their hierarchies,
retrieves all related data (Extractions, Tasks, Links), and packages
them into a ZIP archive compatible with `autosetup`.

Usage:
    python manage.py export_document 1 2 3 --output /path/to/export.zip
"""

import json
import logging
import os
import tempfile
import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand

from badgerdoc.models import (
    document,
    extraction,
    extraction_page,
    task,
    task_extraction,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Export documents and related data (tree) to a ZIP archive"

    def add_arguments(self, parser):
        parser.add_argument(
            "document_ids",
            nargs="+",
            type=int,
            help="Root document IDs to export",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="export.zip",
            help="Path to the output ZIP archive",
        )

    def handle(self, *args, **options):
        root_ids = options["document_ids"]
        output_path = options["output"]

        visited_docs = set()
        docs_to_export = []

        # 1. Tree Discovery
        for doc_id in root_ids:
            self._discover_tree(doc_id, visited_docs, docs_to_export)

        if not docs_to_export:
            self.stdout.write(self.style.WARNING("No documents found for export."))
            return

        self.stdout.write(f"Exporting tree of {len(docs_to_export)} documents...")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for doc in docs_to_export:
                self._export_document(doc, temp_path)

            # Create ZIP archive
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_path)
                        zipf.write(file_path, arcname)

        self.stdout.write(self.style.SUCCESS(f"Successfully exported to {output_path}"))

    def _discover_tree(
        self, doc_id: int, visited: set[int], result: list[document.Document]
    ):
        """Recursively discover document hierarchy."""
        if doc_id in visited:
            return

        try:
            doc = document.Document.objects.get(pk=doc_id)
            visited.add(doc_id)
            result.append(doc)

            # Add children from parent_document relationship
            children = document.Document.objects.filter(parent_document_id=doc_id)
            for child in children:
                self._discover_tree(child.id, visited, result)

        except document.Document.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Document {doc_id} not found."))

    def _export_document(self, doc: document.Document, base_path: Path):
        """Export document, its file, and ALL associated DB records."""
        # Prefix non-root documents to differentiate them
        prefix = "rendition_" if doc.parent_document_id else "root_"
        doc_folder = base_path / f"{prefix}doc_{doc.id}"
        doc_folder.mkdir(parents=True, exist_ok=True)

        # 1. Export File
        doc_filename = None
        if doc.file:
            doc_filename = os.path.basename(doc.file.name)
            file_dest = doc_folder / doc_filename
            with doc.file.open("rb") as f:
                with open(file_dest, "wb") as dest:
                    dest.write(f.read())

        # 2. Base Metadata
        metadata = {
            "id": doc.id,  # Original ID for mapping during import
            "document": {
                "name": doc.name,
                "filename": doc_filename,
                "extension": doc.extension,
                "tags": doc.tags,
                "metadata": doc.metadata,
                "parent_id": doc.parent_document_id,
            },
            "extractions": [],
            "tasks": [],
            "links": [],
        }

        # 3. Export ALL Extractions
        extractions = extraction.Extraction.objects.filter(document=doc)
        for ext in extractions:
            ext_data = {
                "id": ext.id,
                "status": ext.status,
                "comment": ext.comment,
                "tags": ext.tags,
                "pages": [],
                "content": None,
            }

            # ExtractionDocument (JSON content)
            if hasattr(ext, "extraction_document"):
                ext_data["content"] = ext.extraction_document.content

            # ExtractionPages (hOCR)
            pages = extraction_page.ExtractionPage.objects.filter(
                extraction=ext
            ).order_by("page_number")
            for page in pages:
                hocr_filename = f"ext_{ext.id}_page_{page.page_number}.hocr"
                with open(doc_folder / hocr_filename, "w", encoding="utf-8") as f:
                    f.write(page.content)
                ext_data["pages"].append(
                    {
                        "page_number": page.page_number,
                        "content_file": hocr_filename,
                    }
                )

            metadata["extractions"].append(ext_data)

        tasks = task.Task.objects.filter(document=doc)
        for t in tasks:
            task_data = {
                "id": t.id,
                "status_name": t.status.name,
                "tags": t.tags,
                "extraction_ids": list(
                    task_extraction.TaskExtraction.objects.filter(task=t).values_list(
                        "extraction_id", flat=True
                    )
                ),
            }
            metadata["tasks"].append(task_data)

        # Save metadata.json
        with open(doc_folder / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
