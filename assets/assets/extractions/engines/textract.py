import asyncio
import json
import logging
import os

import boto3

from assets.db.models import FileObject
from assets.extractions.base import Extraction

logger = logging.getLogger(__name__)

# AWS Textract configuration
AWS_REGION = os.environ.get("ASSETS_AWS_TEXTRACT_REGION", "us-east-1")
AWS_ACCESS_KEY = os.environ.get("ASSETS_AWS_TEXTRACT_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("ASSETS_AWS_TEXTRACT_SECRET_KEY")

S3_PREFIX = os.getenv("S3_PREFIX")


class TimeoutError(Exception):
    pass


class TextractExtraction(Extraction):
    """
    AWS Textract extraction engine.
    """

    @property
    def enabled(self) -> bool:
        return (
            os.environ.get(
                "ASSETS_TEXTRACT_EXTRACTOR_ENABLED", "false"
            ).lower()
            == "true"
        )

    @property
    def engine(self) -> str:
        return "awstextract"

    @property
    def file_extension(self) -> str:
        return "json"

    @property
    def file_content_type(self) -> str:
        return "application/json"

    def calculate_page_count(self) -> int:
        # Textract returns JSON with all pages in one file
        return 1

    async def wait_for_job_completion(
        self, textract_client, job_id, max_retries=60, delay=5
    ):
        """Poll Textract service until job is complete."""
        for _ in range(max_retries):
            response = textract_client.get_document_text_detection(
                JobId=job_id
            )
            status = response["JobStatus"]

            if status == "SUCCEEDED":
                # Collect all pages of results
                pages_response = [response]
                next_token = response.get("NextToken")

                while next_token:
                    next_page = textract_client.get_document_text_detection(
                        JobId=job_id, NextToken=next_token
                    )
                    pages_response.append(next_page)
                    next_token = next_page.get("NextToken")

                # Combine all blocks from all pages
                combined_response = pages_response[0]
                for page in pages_response[1:]:
                    combined_response["Blocks"].extend(page.get("Blocks", []))

                return combined_response

            if status == "FAILED":
                error_message = response.get("StatusMessage", "Unknown error")
                raise Exception(f"Textract job failed: {error_message}")

            # Wait before checking again
            await asyncio.sleep(delay)

        raise TimeoutError(
            f"Textract job timed out after {max_retries * delay} seconds"
        )

    async def extract(self, file: FileObject) -> None:
        """Start extraction process for the given file ID
        using AWS Textract."""

        logger.info(
            "Starting AWS Textract extraction for file %s",
            file.id,
        )

        if file.extension != ".pdf":
            logger.info(
                "AWS Textract extraction is only supported "
                "for PDF files, skipping file %s",
                file.id,
            )
            return

        started = await self.start(file)
        if not started:
            logger.info(
                "AWS Textract extraction is disabled",
            )
            return

        try:
            if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
                raise ValueError("AWS Textract credentials not configured")

            textract_client = boto3.client(
                "textract",
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
            )
            # TODO: this part is copypasted from badgerdoc_storage

            s3_bucket = (
                f"{S3_PREFIX}-{self.tenant}" if S3_PREFIX else self.tenant
            )
            s3_object = {"Bucket": s3_bucket, "Name": file.path}

            logger.debug("Downloading object from S3 %s", s3_object)

            # Start the analysis process
            # Using Textract's detect_document_text for basic text extraction
            # Can be changed to analyze_document for more advanced features
            start_response = textract_client.start_document_text_detection(
                DocumentLocation={"S3Object": s3_object}
            )

            job_id = start_response["JobId"]
            logger.info(
                "Started asynchronous Textract job %s for file %s",
                job_id,
                file.id,
            )

            # Wait for the job to complete
            extraction_result = await self.wait_for_job_completion(
                textract_client, job_id
            )

            await self.store(
                page_num=1, data=json.dumps(extraction_result).encode("utf-8")
            )

            logger.info(
                "Completed AWS Textract extraction for file %s",
                file.id,
            )

        except Exception:
            logger.exception(
                "Error during AWS Textract extraction for file %s", file.id
            )
            raise
        finally:
            await self.finish()
