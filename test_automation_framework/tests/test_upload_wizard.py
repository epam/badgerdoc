import uuid
import pytest
from playwright.sync_api import Page, expect
from helpers.files.file_client_frontend import FrontendFileHelper
from logging import getLogger

logger = getLogger(__name__)


class TestUploadWizard:
    def run_upload_workflow(
        self,
        page: Page,
        frontend_file_helper: FrontendFileHelper,
        num_files: int,
        file_tracker,
        client,
        jobs_client,
        dataset_type: str = "none",  # "none", "existing", "new"
        dataset_name: str = None,
        tmp_path=None,
    ):
        created_files = file_tracker[0]

        # Open wizard
        logger.info("Open wizard")
        page.get_by_role("button", name="Upload Wizard").click()

        # Upload files
        temp_files = frontend_file_helper.prepare_temp_files(tmp_path, num_files=num_files)
        frontend_file_helper.upload_files(page, temp_files, file_tracker=created_files, client=client)

        # Dataset choice
        if dataset_type == "none":
            page.locator("label:has-text('No') div").nth(1).click()
            page.get_by_role("button", name="Next").click()
        elif dataset_type == "existing":
            page.locator("label:has-text('Existing dataset') div").nth(1).click()
            page.locator(".uui-icon.uui-enabled.uui-icon-dropdown").click()
            page.get_by_text(dataset_name, exact=True).click()
            page.get_by_role("button", name="Next").click()
        elif dataset_type == "new":
            page.locator("label:has-text('New dataset') div").nth(1).click()
            page.get_by_role("textbox", name="Dataset name").fill(dataset_name)
            page.get_by_role("button", name="Next").click()
        else:
            raise ValueError(f"Unknown dataset_type {dataset_type}")

        # Choose pipeline
        logger.info("Choose pipeline")
        page.get_by_text("No need for preprocessor").click()
        page.get_by_role("button", name="Next").click()

        # Fill job name
        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        page.get_by_role("textbox", name="Job name").fill(job_name)

        # Select pipeline dropdown
        page.locator(".uui-icon.uui-enabled.uui-icon-dropdown").click()
        page.get_by_text("print", exact=True).click()

        # Start extraction
        logger.info("Start extraction")
        page.get_by_role("button", name="Start Extraction").click()
        page.wait_for_url("**/jobs/**", timeout=10000)

        # Wait for job to finish
        jobs = jobs_client.search_jobs()
        job_id = next((j["id"] for j in jobs["data"] if j["name"] == job_name), None)
        assert job_id, f"Job with name {job_name} not found!"
        jobs_client.poll_until_finished(job_id, timeout_seconds=180)
        page.reload()
        expect(page.get_by_text("Finished")).to_be_visible(timeout=10000)

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_without_dataset(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, num_files
    ):
        page = logged_in_page
        created_files, client = file_tracker
        frontend_file_helper = FrontendFileHelper()
        self.run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="none",
            tmp_path=tmp_path,
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_existing_dataset(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, dataset_tracker, num_files
    ):
        page = logged_in_page
        created_files, client = file_tracker
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        first_resp = dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        assert "successfully created" in first_resp["detail"].lower()

        frontend_file_helper = FrontendFileHelper()
        self.run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="existing",
            dataset_name=dataset_name,
            tmp_path=tmp_path,
        )

    @pytest.mark.parametrize("num_files", [1, 3])
    def test_upload_documents_new_dataset(
        self, logged_in_page: Page, file_tracker, tmp_path, jobs_client, file_client, dataset_tracker, num_files
    ):
        page = logged_in_page
        created_files, client = file_tracker
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        created_datasets.append(dataset_name)

        frontend_file_helper = FrontendFileHelper()
        self.run_upload_workflow(
            page,
            frontend_file_helper,
            num_files,
            file_tracker,
            client,
            jobs_client,
            dataset_type="new",
            dataset_name=dataset_name,
            tmp_path=tmp_path,
        )
