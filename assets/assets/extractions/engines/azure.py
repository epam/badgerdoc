import json
import logging
import os

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from assets.db.models import FileObject
from assets.extractions.base import Extraction

logger = logging.getLogger(__name__)

# Azure Document Intelligence configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.environ.get(
    "ASSETS_AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
)
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.environ.get(
    "ASSETS_AZURE_DOCUMENT_INTELLIGENCE_KEY"
)
AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID = os.environ.get(
    "ASSETS_AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID", "prebuilt-layout"
)


class AzureExtraction(Extraction):
    """
    Azure extraction engine.
    """

    @property
    def enabled(self) -> bool:
        return (
            os.environ.get("ASSETS_AZURE_EXTRACTOR_ENABLED", "false").lower()
            == "true"
        )

    @property
    def engine(self) -> str:
        return "azuredi"

    @property
    def file_extension(self) -> str:
        return "json"

    @property
    def file_content_type(self) -> str:
        return "application/json"

    def calculate_page_count(self) -> int:
        # Azure returns JSON with all pages in one file
        return 1

    async def extract(self, file: FileObject) -> None:
        """Start extraction process for the
        given file ID using Azure Document Intelligence."""

        logger.info(
            "Starting azure extraction for file %s",
            file.id,
        )

        if file.extension != ".pdf":
            logger.info(
                "Azure extraction is only supported for PDF files, "
                "skipping file %s",
                file.id,
            )
            return

        started = await self.start(file)
        if not started:
            logger.info(
                "Azure extraction is disabled",
            )
            return
        file_signed_url = await self.gen_signed_url(file)

        try:
            if not (
                AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
                and AZURE_DOCUMENT_INTELLIGENCE_KEY
            ):
                raise ValueError(
                    "Azure Document Intelligence credentials not configured"
                )
            # Initialize the Document Intelligence client
            document_intelligence_client = DocumentIntelligenceClient(
                endpoint=AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(AZURE_DOCUMENT_INTELLIGENCE_KEY),
            )

            # Start the analysis process
            async with document_intelligence_client:
                # Process the document using the URL directly
                poller = (
                    await document_intelligence_client.begin_analyze_document(
                        model_id=AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID,
                        body={"urlSource": file_signed_url},
                    )
                )

                analyze_result = await poller.result()
                extraction_result = analyze_result.as_dict()

                await self.store(
                    page_num=1,
                    data=json.dumps(extraction_result).encode("utf-8"),
                )

                logger.info(
                    "Completed Azure extraction for file %s",
                    file.id,
                )

        except Exception:
            logger.exception(
                "Error during Azure extraction for file %s", file.id
            )
            raise
        finally:
            await self.finish()
